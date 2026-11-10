import hashlib
from collections import defaultdict
from typing import Dict, List, Optional
from django.conf import settings as django_settings
from django.http import JsonResponse
from .services import build_location_payload
from network_topology.models import Node, Link
from network_topology.models import Institution
from .models import UIString
from .translation import ensure_institution_popup_translations, ensure_ui_string_translations


# Values of the "trust_level" property GRENML-Repository publishes
TRUST_VERIFIED = "verified"
TRUST_AI_GENERATED = "ai_generated"

# Where the data notice's "How the data is maintained" link points
DATA_NOTICE_URL = (
    "https://github.com/grenmap/GRENML-Repository#verified-and-ai-generated-networks"
)


PREDEFINED_COLORS = {
    # EXISTENTES
    "RedCLARA": "#2E86DE",
    "AmLight": "#7CB342",
    "CEDIA": "#FB8C00",
    "REUNA": "#D84343",

    # NOVAS
    "RNP": "#5E60CE",
    "AARNet": "#00897B",
    "Arnes": "#6D4C41",
    "FCCN": "#3949AB",
    "FUNET": "#00838F",
    "GARR": "#AD1457",
    "HEAnet": "#558B2F",
    "KAUST": "#8D6E63",
    "ARENA PAC": "#F9A825",
    "AER": "#7E57C2",
    "ANA": "#00ACC1",
    "APREX": "#EF6C00",
    "GEANT IC 1": "#546E7A",
    "INDIGO": "#3F51B5",
    "SANREN/TENET": "#2E7D32",
    "Guam-SG Connectivity Consortium": "#5E35B1",
    "NII 100G": "#455A64"
}

def parent_menu_of(institution: Institution) -> int:
    """PREN(1)/NREN(2) menu id from the institution's "tag" property."""
    for p in institution.properties.all():
        if p.name == "tag":
            value = p.value.lower()

            if value == "nren":
                return 2

            if value == "pren":
                return 1

    return 1


def get_parent_menu(network_name: str) -> int:
    institution = Institution.objects.filter(name=network_name).first()

    if not institution:
        return 1

    return parent_menu_of(institution)

def generate_color(name: str) -> str:
    if name in PREDEFINED_COLORS:
        return PREDEFINED_COLORS[name]

    hash = hashlib.md5(name.encode()).hexdigest()
    return f"#{hash[:6]}"

def menu_group(request):
    data = [
        {
            "id": 1,
            "name": "Menu Group TESTE",
            "simultaneous_context": True
        }
    ]
    return JsonResponse(data, safe=False)

def menu(request):
    data = [
        {
            "id": 1,
            "name": "PRENs",
            "hierarchy_level": 0,
            "active": True,
            "group": 1
        },
        {
            "id": 2,
            "name": "NRENs",
            "hierarchy_level": 0,
            "active": True,
            "group": 1
        }
    ]

    return JsonResponse(data, safe=False)

def institutions_by_name() -> Dict[str, List[Institution]]:
    """
    Every Institution, with its properties, grouped by name -- loaded
    once per request instead of once per node.
    """
    by_name = defaultdict(list)
    for institution in Institution.objects.prefetch_related('properties').order_by('pk'):
        by_name[institution.name].append(institution)
    return by_name


def get_popup_institutions(
    node: Node, institutions: Dict[str, List[Institution]],
) -> List[Institution]:
    """
    Returns the Institutions from the node's "networks" property.
    "networks" is the same semicolon-separated, curated list of networks
    a node actually belongs to that already drives the map's tag
    sidebar -- unlike node.owners, which GRENML import also populates
    with the whole topology's declared owner on every node regardless
    of relevance (e.g. it put RedCLARA on every single node, including
    ones with no real connection to it).

    Networks without popup text are included too: the popup still shows
    their name, how far to trust their data and when it last changed.

    A node may belong to more than one network; each gets its own tab
    in the map popup rather than only the first one winning -- the
    frontend is responsible for picking which of them to show based
    on the active PREN/NREN menu (see build_popup_fields'
    "parent_menu" field on each entry).
    """
    network_names = set()
    for p in node.properties.all():
        if p.name == "networks" and p.value:
            network_names.update(n.strip() for n in p.value.split(';') if n.strip())

    found = [
        institution
        for name in network_names
        for institution in institutions.get(name, [])
    ]
    return sorted(found, key=lambda institution: institution.pk)


def property_value(institution: Institution, name: str) -> Optional[str]:
    for p in institution.properties.all():
        if p.name == name and p.value:
            return p.value
    return None


def provenance_fields(institution: Institution) -> dict:
    """
    How far to trust a network's data and when it last changed, from
    the properties GRENML-Repository's generator publishes. A network
    without them counts as AI-generated: that's where the data came
    from until someone verifies it.
    """
    verified = property_value(institution, "trust_level") == TRUST_VERIFIED
    return {
        "trust_level": TRUST_VERIFIED if verified else TRUST_AI_GENERATED,
        "verified_by": property_value(institution, "verified_by") if verified else None,
        "verified_on": property_value(institution, "verified_on") if verified else None,
        "data_updated_on": property_value(institution, "data_updated_on"),
        "data_updated_url": property_value(institution, "data_updated_url"),
    }


def build_popup_fields(node: Node, institutions: Dict[str, List[Institution]]) -> dict:
    return {
        "popup_institutions": [
            {
                "name": institution.name,
                "description": institution.popup_summary,
                "overlayed_popup_content": institution.popup_content,
                # Same PREN(1)/NREN(2) menu id used by the map's own
                # PREN/NREN filter (see get_parent_menu) -- lets the
                # frontend show only the institution(s) matching
                # whichever menu is currently selected, instead of
                # every owner regardless of the active filter.
                "parent_menu": parent_menu_of(institution),
                **provenance_fields(institution),
                "translations": [
                    {
                        "language_code": t.language_code,
                        "description": t.summary,
                        "overlayed_popup_content": t.full_content,
                    }
                    for t in ensure_institution_popup_translations(institution)
                ],
            }
            for institution in get_popup_institutions(node, institutions)
        ],
    }


def location(request):
    nodes = Node.objects.prefetch_related('properties')
    institutions = institutions_by_name()

    locations = []

    for n in nodes:
        locations.append({
            "id": n.id,
            "name": n.name,
            "latitude": str(n.latitude),
            "longitude": str(n.longitude),
            "active": True,
            **build_popup_fields(n, institutions),
        })

    return JsonResponse(locations, safe=False)

def tag(request):
    nodes = Node.objects.all().order_by("id")

    tags_map = {}
    tag_id = 1

    for n in nodes:
        for p in n.properties.all():
            if p.name != "networks":
                continue

            if not p.value:
                continue

            for net in p.value.split(';'):
                net = net.strip()

                if net not in tags_map:
                    tags_map[net] = {
                        "id": tag_id,
                        "name": net,
                        "description": "",
                        "color": generate_color(net),
                        "active": True,
                        "parent_menu": get_parent_menu(net),
                        "related_locations": [],
                        "sidebar_content": "",
                        "overlayed_popup_content": ""
                    }
                    tag_id += 1

                tags_map[net]["related_locations"].append(n.id)

    return JsonResponse(list(tags_map.values()), safe=False)

def tag_relationship(request):
    return JsonResponse([], safe=False)

def settings(request):
    return JsonResponse([{
            "id":0,
            "map_name":"REN MAP",
            "map_style":"d",
            "inherit_children_tag_locations":False,
            "cluster_close_tags":True,
            "initial_zoom_level":0,
            "initial_latitude":"14.57950740769543962472",
            "initial_longitude":"-55.92525392265913808387",
            "link_feature":True,
            "hide_menu_group_when_unique":True,
            "footer_file": None,
            "correction_email": django_settings.MAP_CORRECTION_EMAIL,
            # ChameleonMap's first-visit tutorial is Portuguese-only;
            # REN Map's audience is international, so it's turned off.
            "onboarding_enabled": False,
            # Topologies here are semi-automatic/AI-extracted: tell
            # visitors on their first visit, then keep a reminder.
            "data_notice_enabled": True,
            "data_notice_url": DATA_NOTICE_URL,
        }], safe=False)

def link(request):
    links = Link.objects.all().order_by("id")

    result = []
    link_id = 1

    for l in links:
        n1 = l.node_a
        n2 = l.node_b

        networks = []
        for p in l.properties.all():
            if p.name == "networks" and p.value:
                networks = [n.strip() for n in p.value.split(';') if n.strip()]
                break

        result.append({
            "id": link_id,
            "display_name": f"{n1.name} - {n2.name}",
            "popup_description": "",
            "curvature": "2.000",
            "weight": 5,
            "dashed": False,
            "straight_link": False,
            "invert_link": False,
            "location_1": n1.id,
            "location_2": n2.id,
            "networks": networks
        })

        link_id += 1

    return JsonResponse(result, safe=False)

def links_group(request):
    links = Link.objects.all().order_by("id")

    group_map = {}
    group_id = 1

    for l in links:
        for p in l.properties.all():
            if p.name != "networks" or not p.value:
                continue

            for net in p.value.split(';'):
                net = net.strip()

                if net not in group_map:
                    group_map[net] = {
                        "id": group_id,
                        "name": net,
                        "links_color": generate_color(net),
                        "opacity": "0.600",
                        "sidebar_content": "",
                        #"parent_menu": get_parent_menu(net),
                    }
                    group_id += 1

    return JsonResponse(list(group_map.values()), safe=False)

def kml_shape(request):
    return JsonResponse([], safe=False)

def uistrings(request):
    result = []

    for ui_string in UIString.objects.all():
        translations = ensure_ui_string_translations(ui_string)

        result.append({
            "key": ui_string.key,
            "text": ui_string.text,
            "translations": [
                {
                    "language_code": t.language_code,
                    "text": t.text,
                }
                for t in translations
            ],
        })

    return JsonResponse(result, safe=False)