from __future__ import annotations
from abc import ABC
import xml.etree.ElementTree as ET
from pathlib import Path
from shapely.geometry import Polygon, Point, LineString, LinearRing

class KMLTag(ABC):
    def __init__(self, namespace: str | None = '', **kwargs):
        self.namespace = namespace
        self.attributes = kwargs
        self.children: list[KMLTag] = []

    def __repr__(self) -> str:
        return type(self).__name__.replace("KML", '')

    def __str__(self) -> str:
        tag_name = self.__repr__()
        tag_body = '\n'

        for att_name, att_body in self.attributes.items():
            if att_name and att_body:
                tag_body += f'<{att_name}>{att_body}</{att_name}>\n'

        for child in self.children:
            tag_body += child.__str__() + '\n'

        return f"<{tag_name}>{tag_body}</{tag_name}>"

    def _add_tag(self, tag: KMLTag) -> None:
        self.children.append(tag)


class KMLFolder(KMLTag):
    pass

class KMLDocument(KMLTag):
    pass


class KMLPlacemark(KMLTag):
    def __init__(self, geometry: Point | Polygon | LineString | LinearRing,  *args, **kwargs):
        super().__init__(*args, **kwargs);
        self.geometry = geometry

    def __str__(self) -> str:
        tag_name = self.__repr__()
        tag_body = '\n'

        for att_name, att_body in self.attributes.items():
            if att_name and att_body:
                tag_body += f'<{att_name}>{att_body}</{att_name}>\n'

        string = f"<{tag_name}>{tag_body}"

        if isinstance(self.geometry, Point):
            string += f"<Point>{self.geometry.x},{self.geometry.y}"
            
            if self.geometry.length == 3:
                string += f",{self.geometry.z}"

            string += "</Point>\n"

        elif isinstance(self.geometry, Polygon):
            string += f"<Polygon>\n" 

            string += "<outerBoundaryIs>\n"
            string += "<LinearRing>"
            
            for point in self.geometry.exterior.coords:
                string += f'{point[0]},{point[1]}'

                if len(point) == 3:
                    string += f',{point[2]}'

                string += ' '

            string += "</LinearRing>\n"
            string += "</outerBoundaryIs>\n"

            for hole in self.geometry.interiors:
                string += "<innerBoundaryIs>\n"
                string += "<LinearRing>"
                
                for point in hole.coords:
                    string += f'{point[0]},{point[1]}'

                    if len(point) == 3:
                        string += f',{point[2]}'

                    string += ' '

                string += "</LinearRing>\n"
                string += "</innerBoundaryIs>\n"

            string += "</Polygon>\n"

        elif isinstance(self.geometry, LinearRing):
            string += f"<LinearRing>"

            for point in self.geometry.coords:
                string += f'{point[0]},{point[1]}'

                if len(point) == 3:
                    string += f',{point[2]}'

                string += ' '

            string += "</LinearRing>\n"

        elif isinstance(self.geometry, LineString):
            string += f"<LineString>"

            for point in self.geometry.coords:
                string += f'{point[0]},{point[1]},{point[2]} '

            string += "</LineString>\n"
        
        return string + f"</{tag_name}>"

def kml_parse_placemark(tree_node, namespace: str | None = '') -> KMLPlacemark:
    placemark_name = tree_node.find(f'{namespace}name')
    placemark_description = tree_node.find(f'{namespace}description')

    geometry = None

    geometry_tag = tree_node.find(f'{namespace}Point')

    if geometry_tag is not None:
        geometry = Point([float(v) for v in geometry_tag.find(f'{namespace}coordinates').text.split(',')])

    geometry_tag = tree_node.find(f'{namespace}Polygon')

    if geometry_tag is not None:
        outer_points_tag = geometry_tag.find(f'{namespace}outerBoundaryIs')
        inner_points_tag = geometry_tag.findall(f'{namespace}innerBoundaryIs')
    
        geometry = Polygon()

        outer_points = []
        outer_points_string = outer_points_tag.find(f"{namespace}LinearRing").find(f'{namespace}coordinates').text

        for pair in outer_points_string.replace('\n', ' ').replace('\t', ' ').split(' '):
            if not pair: continue
            
            outer_points.append([float(val) for val in pair.split(',')])
        
        inner_points = []
        
        for inner in inner_points_tag:
            hole = [] 
            inner_points_string = inner.find(f'{namespace}LinearRing').find(f'{namespace}coordinates').text

            for pair in inner_points_string.replace('\n', ' ').replace('\t', ' ').split(' '):
                if not pair: continue
                
                hole.append([float(val) for val in pair.split(',')])

            inner_points.append(hole)

        geometry = Polygon(outer_points, inner_points)

    geometry_tag = tree_node.find(f'{namespace}LinearRing')

    if geometry_tag is not None:
        points = []
        points_string = geometry_tag.find(f'{namespace}coordinates').text

        for pair in points_string.replace('\n', ' ').replace('\t', ' ').split(' '):
            if not pair: continue
            
            points.append([float(val) for val in pair.split(',')])

        geometry = LinearRing(points)

    geometry_tag = tree_node.find(f'{namespace}LineString')

    if geometry_tag is not None:
        points = []
        points_string = geometry_tag.find(f'{namespace}coordinates').text

        for pair in points_string.replace('\n', ' ').replace('\t', ' ').split(' '):
            if not pair: continue
            
            points.append([float(val) for val in pair.split(',')])

        geometry = LineString(points)

    return KMLPlacemark(
            geometry=geometry,
            name=placemark_name.text if placemark_name is not None else None,
            description=placemark_description.text if placemark_description is not None else None
            )

def kml_parse_file(tree_node, tag: KMLTag) -> KMLTag:

    for child in tree_node:

        element: KMLTag | None = None

        match child.tag:
            case x if x.endswith('Folder') or x.endswith('Document'):

                container_name = child.find(f'{tag.namespace}name')
                container_description = child.find(f'{tag.namespace}description')

                kml_tag = KMLFolder if child.tag.endswith("Folder") else KMLDocument

                element = kml_tag(
                    namespace   = tag.namespace,
                    name        = container_name.text if container_name is not None else None,
                    description = container_description.text if container_description is not None else None
                )

            case x if x.endswith('Placemark'):
                placemark = kml_parse_placemark(child, tag.namespace)
                tag._add_tag(placemark)

            case _:
                kml_parse_file(child, tag)

        if not element:
            continue

        tag._add_tag(element)
        kml_parse_file(child, element)

    return tag


class KMLFile(object):
    def __init__(self, filepath: Path | str) -> None:
        self.filepath = filepath

    def __enter__(self):
        kml_tree = ET.parse(self.filepath)
        kml_root = kml_tree.getroot()

        namespace = kml_root.tag[: kml_root.tag.index('}') + 1]

        document = KMLTag(namespace=namespace)
        return kml_parse_file(kml_root, document).children.pop()

    def __exit__(self, exec_type, exec_val, exec_tb) -> None:
        return 
        
def main():

    with KMLFile('./res/file-5.kml') as kml_file:
        print(kml_file)

    return

if __name__ == "__main__":
    main()
