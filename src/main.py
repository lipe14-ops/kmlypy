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

    @property
    def name(self) -> str | None:
        return self.attributes.get('name')

    @property
    def description(self) -> str | None:
        return self.attributes.get('description')

    @name.setter
    def name(self, value: str) -> str:
        self.attributes['name'] = value
        return value

    @description.setter
    def description(self, value: str) -> str:
        self.attributes['description'] = value
        return value

    def __repr__(self) -> str:
        tag_name = type(self).__name__.replace("KML", '')
        return f'<KMLTag {hex(id(self))} {self.namespace}{tag_name}>'

    def as_kml(self) -> str:
        tag_name = type(self).__name__.replace("KML", '')
        tag_body = '\n'

        for att_name, att_body in self.attributes.items():
            if att_name and att_body:
                tag_body += f'<{att_name}>{att_body}</{att_name}>\n'

        for child in self.children:
            tag_body += child.as_kml() + '\n'

        return f"<{tag_name}>{tag_body}</{tag_name}>"

    def add_tag(self, tag: KMLTag) -> KMLTag:
        self.children.append(tag)
        return tag


class KMLFolder(KMLTag):

    def path(self, path: str) -> KMLFolder | KMLPlacemark:
        dirs = list(filter(lambda x: x, path.split('/')))

        if not dirs:
            return self

        dir = dirs.pop(0)
            
        for child in self.children:
            if child.name == dir:
                if isinstance(child, KMLFolder):
                    child_path = '/'.join(dirs)
                    return child.path(child_path)

                elif isinstance(child, KMLPlacemark):
                    return child
            
        raise ValueError("FOLDER NOT FOUND")


class KMLDocument(KMLFolder):
    pass

class KMLPlacemark(KMLTag):
    def __init__(self, geometry: Point | Polygon | LineString | LinearRing,  *args, **kwargs):
        super().__init__(*args, **kwargs);
        self.geometry = geometry

    def as_kml(self) -> str:
        tag_name = type(self).__name__.replace("KML", '')
        tag_body = '\n'

        for att_name, att_body in self.attributes.items():
            if att_name and att_body:
                tag_body += f'<{att_name}>{att_body}</{att_name}>\n'

        string = f"<{tag_name}>{tag_body}"

        if isinstance(self.geometry, Point):
            string += f"<Point>\n"
            string += "<coordinates>"
            
            string += f"{self.geometry.x},{self.geometry.y}"
            
            if self.geometry.length == 3:
                string += f",{self.geometry.z}"

            string += "</coordinates>\n"
            string += "</Point>\n"

        elif isinstance(self.geometry, Polygon):
            string += f"<Polygon>\n" 

            string += "<outerBoundaryIs>\n"
            string += "<LinearRing>\n"
            string += "<coordinates>"
            
            for point in self.geometry.exterior.coords:
                string += f'{point[0]},{point[1]}'

                if len(point) == 3:
                    string += f',{point[2]}'

                string += ' '

            string += "</coordinates>\n"
            string += "</LinearRing>\n"
            string += "</outerBoundaryIs>\n"

            for hole in self.geometry.interiors:
                string += "<innerBoundaryIs>\n"
                string += "<LinearRing>\n"
                string += "<coordinates>"
                
                for point in hole.coords:
                    string += f'{point[0]},{point[1]}'

                    if len(point) == 3:
                        string += f',{point[2]}'

                    string += ' '

                string += "</coordinates>"
                string += "</LinearRing>\n"
                string += "</innerBoundaryIs>\n"

            string += "</Polygon>\n"

        elif isinstance(self.geometry, LinearRing):
            string += f"<LinearRing>\n"
            string += "<coordinates>"

            for point in self.geometry.coords:
                string += f'{point[0]},{point[1]}'

                if len(point) == 3:
                    string += f',{point[2]}'

                string += ' '

            string += "</coordinates>\n"
            string += "</LinearRing>\n"

        elif isinstance(self.geometry, LineString):
            string += f"<LineString>\n"
            string += "<coordinates>"

            for point in self.geometry.coords:
                string += f'{point[0]},{point[1]},{point[2]} '

            string += "</coordinates>\n"
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
               element = kml_parse_placemark(child, tag.namespace)

            case _:
                kml_parse_file(child, tag)

        if not element:
            continue

        tag.add_tag(element)
        kml_parse_file(child, element)

    return tag


class KMLFile(object):
    def __init__(self, filepath: Path | str, autosave: bool = True, mode: str = 'r', namespace: str = '') -> None:
        self.filepath = filepath
        self.autosave = autosave
        self.mode = mode
        self.document: KMLDocument = KMLDocument()
        self.namespace = namespace

    def __enter__(self) -> KMLFile:
        try:
            kml_tree = ET.parse(self.filepath)
            kml_root = kml_tree.getroot()

            try:
                self.namespace = kml_root.tag[: kml_root.tag.index('}') + 1]
            except ValueError: 
                self.namespace = ''

            document = KMLTag(namespace=self.namespace)
            file_content = kml_parse_file(kml_root, document).children.pop()

            if not isinstance(file_content, KMLDocument):
                raise ValueError("INVALID FILE FORMAT")

            self.document = file_content

        except FileNotFoundError as error:
            if self.mode in ('r', 'rb'):
                raise error

        return self

    def __exit__(self, exec_type, exec_val, exec_tb) -> None:
        if self.autosave and self.mode in ('w', 'wb'):
            self.save()

    def save(self, filepath: str | Path | None = None) -> None:
        filepath = filepath if filepath else self.filepath

        header = f'<?xml version="1.0" encoding="UTF-8"?>\n'
        data = header
        data += "<kml"
        data += '' if not self.namespace else f' xmlns="{self.namespace}"'
        data += '>\n'

        data += self.document.as_kml()
        
        data += '\n</kml>'

        kml_tree = ET.fromstring(data)
        ET.indent(kml_tree)

        with open(filepath, 'w') as kml_file:
            kml_file.write(
                    header + ET.tostring(kml_tree, encoding='unicode')
                    )

def main():

    with KMLFile('./res/file-7.kml', mode='w') as kml_file:
        kml_file.document.name = "CAVALO"

        pasta = kml_file.document.add_tag(
                KMLFolder(name="PASTA", description="PASTA TOP DEMAIS")
                )

        pasta.add_tag(
                KMLPlacemark(
                    name="PONTO",
                    geometry=Point(10, 10)
                    )
                )

        # kml_file.save()

    with KMLFile('./res/file-7.kml') as kml_file:
        polygon = kml_file.document.path('/PASTA/PONTO')

        if not isinstance(polygon, KMLPlacemark):
            raise ValueError("NAO E POLIGONO")

        print(polygon.geometry.area)

    return

if __name__ == "__main__":
    main()
