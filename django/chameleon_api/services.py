from network_topology.models import Node

def get_nodes():
    return Node.objects.all()

def build_tags(nodes):
    tags = {}
    tag_id = 1

    for node in nodes:
        networks = getattr(node, 'networks', None)

        if not networks:
            continue

        for net in networks.split(';'):
            net = net.strip()

            if net not in tags:
                tags[net] = {
                    "id": tag_id,
                    "name": net
                }
                tag_id += 1

    return tags

def build_locations(nodes):
    locations = []
    location_id = 1

    for node in nodes:
        locations.append({
            "id": location_id,
            "name": node.name,
            "lat": node.latitude,
            "lng": node.longitude,
        })
        location_id += 1

    return locations

def build_tag_relationships(nodes, tags):
    relationships = []
    location_id = 1

    for node in nodes:
        networks = getattr(node, 'networks', None)

        if not networks:
            location_id += 1
            continue

        for net in networks.split(';'):
            net = net.strip()

            tag = tags.get(net)

            if tag:
                relationships.append({
                    "tag": tag["id"],
                    "location": location_id
                })

        location_id += 1

    return relationships

def build_location_payload():
    nodes = get_nodes()

    tags = build_tags(nodes)
    locations = build_locations(nodes)
    relationships = build_tag_relationships(nodes, tags)

    return {
        "locations": locations,
        "tags": list(tags.values()),
        "tagRelationships": relationships
    }