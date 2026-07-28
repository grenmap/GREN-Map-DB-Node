import hashlib
from django.http import JsonResponse
from .services import build_location_payload
from network_topology.models import Node, Link
from network_topology.models import Institution


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

def get_parent_menu(network_name: str) -> int:
    institution = Institution.objects.filter(name=network_name).first()

    if not institution:
        return 1

    for p in institution.properties.all():
        if p.name == "tag":
            value = p.value.lower()

            if value == "nren":
                return 2

            if value == "pren":
                return 1

    return 1

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

def location(request):
    nodes = Node.objects.all()

    locations = []
    
    for n in nodes:
        locations.append({
            "id": n.id,
            "name": n.name,
            "description": "",
            "latitude": str(n.latitude),
            "longitude": str(n.longitude),
            "overlayed_popup_content": "",
            "active": True
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
            "footer_file": None
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