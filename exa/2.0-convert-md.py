"""
Conversor HTML a Markdown MEJORADO
Optimizado para documentación técnica legacy (HTML 4.0, iso-8859-1, etc.)
"""

import os
import re
import logging
import chardet
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import html2text

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImprovedHTMLtoMarkdownConverter:
    """
    Conversor mejorado HTML → Markdown para documentación técnica legacy
    Maneja: encoding automático, entidades HTML, tablas complejas, etc.
    """
    
    def __init__(self, input_dir: str = "html", output_dir: str = "md"):
        """
        Inicializar conversor mejorado
        
        Args:
            input_dir: Directorio con archivos HTML
            output_dir: Directorio de salida para Markdown
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Configurar html2text con mejores opciones para tablas
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = False  # Mantener referencias a imágenes
        self.h2t.ignore_emphasis = False
        self.h2t.body_width = 0  # Sin límite de ancho
        self.h2t.single_line_break = False
        self.h2t.mark_code = True  # Marcar código correctamente
        self.h2t.wrap_links = False  # No envolver enlaces
        self.h2t.default_image_alt = ""  # Sin alt text por defecto
        
        # Tags a eliminar (no aportan contenido útil para RAG)
        self.tags_to_remove = [
            'script', 'style', 'nav', 'header', 'footer', 
            'aside', 'iframe', 'noscript', 'canvas',
            'button', 'form', 'input', 'select', 'textarea',
            'link'  # CSS links
        ]
        
        # Atributos a eliminar
        self.attrs_to_remove = [
            'class', 'id', 'style', 'onclick', 'onload',
            'align', 'valign', 'bgcolor', 'width', 'height',
            'border', 'cellpadding', 'cellspacing', 'nosave',
            'vspace', 'hspace'
        ]
        
        self.stats = {
            'processed': 0,
            'failed': 0,
            'skipped': 0,
            'total_size': 0,
            'encoding_issues': 0
        }
    
    def detect_encoding(self, file_path: Path) -> str:
        """
        Detectar encoding del archivo HTML
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Nombre del encoding detectado
        """
        try:
            # Leer primeros bytes para detectar
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)  # Leer primeros 10KB
            
            # Detectar con chardet
            result = chardet.detect(raw_data)
            detected_encoding = result['encoding']
            confidence = result['confidence']
            
            # Si la confianza es baja, intentar con meta tag
            if confidence < 0.7:
                try:
                    # Buscar meta charset en los primeros bytes
                    raw_text = raw_data.decode('latin-1', errors='ignore')
                    charset_match = re.search(r'charset=(["\']?)([a-zA-Z0-9-]+)\1', raw_text, re.IGNORECASE)
                    if charset_match:
                        meta_encoding = charset_match.group(2)
                        logger.debug(f"Encoding desde meta tag: {meta_encoding}")
                        return meta_encoding
                except:
                    pass
            
            logger.debug(f"Encoding detectado: {detected_encoding} (confianza: {confidence:.2f})")
            return detected_encoding if detected_encoding else 'utf-8'
            
        except Exception as e:
            logger.warning(f"Error detectando encoding, usando UTF-8: {e}")
            return 'utf-8'
    
    def read_html_with_encoding(self, file_path: Path) -> str:
        """
        Leer HTML con detección automática de encoding
        
        Args:
            file_path: Ruta del archivo
            
        Returns:
            Contenido HTML como string
        """
        # Detectar encoding
        encoding = self.detect_encoding(file_path)
        
        # Intentar leer con el encoding detectado
        encodings_to_try = [encoding, 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for enc in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=enc, errors='replace') as f:
                    content = f.read()
                logger.debug(f"Archivo leído exitosamente con encoding: {enc}")
                return content
            except Exception as e:
                logger.debug(f"Fallo con encoding {enc}: {e}")
                continue
        
        # Si todo falla, leer como binario y decodificar con replace
        logger.warning(f"Todos los encodings fallaron, usando lectura forzada")
        self.stats['encoding_issues'] += 1
        with open(file_path, 'rb') as f:
            return f.read().decode('utf-8', errors='replace')
    
    def extract_metadata(self, soup: BeautifulSoup, file_path: Path) -> Dict[str, str]:
        """
        Extraer metadata del HTML (mejorado para HTML legacy)
        
        Args:
            soup: Objeto BeautifulSoup
            file_path: Ruta del archivo original
            
        Returns:
            Diccionario con metadata extraída
        """
        metadata = {}
        
        # Título (múltiples fuentes)
        title = None
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find('meta', attrs={'property': 'og:title'}):
            title = soup.find('meta', attrs={'property': 'og:title'}).get('content')
        elif soup.find('h1'):
            # Extraer texto del h1, eliminando imágenes
            h1 = soup.find('h1')
            for img in h1.find_all('img'):
                img.decompose()
            title = h1.get_text().strip()
        
        if title:
            metadata['title'] = ' '.join(title.split())
        else:
            metadata['title'] = file_path.stem
        
        # Descripción - buscar en varios lugares
        desc = None
        desc_meta = soup.find('meta', attrs={'name': 'description'}) or \
                    soup.find('meta', attrs={'name': 'Description'}) or \
                    soup.find('meta', attrs={'property': 'og:description'})
        
        if desc_meta and desc_meta.get('content'):
            desc = desc_meta.get('content')
        elif soup.find('h2'):
            # Usar primer h2 como descripción si no hay meta
            desc = soup.find('h2').get_text().strip()
        
        if desc:
            metadata['description'] = ' '.join(desc.split())
        
        # Keywords
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'}) or \
                       soup.find('meta', attrs={'name': 'Keywords'})
        if keywords_meta and keywords_meta.get('content'):
            metadata['keywords'] = keywords_meta.get('content')
        
        # Autor
        author_meta = soup.find('meta', attrs={'name': 'author'}) or \
                      soup.find('meta', attrs={'name': 'Author'}) or \
                      soup.find('meta', attrs={'property': 'article:author'})
        if author_meta and author_meta.get('content'):
            metadata['author'] = author_meta.get('content')
        
        # Fecha de publicación
        date_meta = soup.find('meta', attrs={'property': 'article:published_time'}) or \
                    soup.find('meta', attrs={'name': 'date'}) or \
                    soup.find('time')
        if date_meta:
            if date_meta.name == 'time' and date_meta.get('datetime'):
                metadata['date'] = date_meta.get('datetime')
            elif date_meta.get('content'):
                metadata['date'] = date_meta.get('content')
        
        # Generador (útil para saber origen del HTML)
        generator_meta = soup.find('meta', attrs={'name': 'GENERATOR'}) or \
                        soup.find('meta', attrs={'name': 'generator'})
        if generator_meta and generator_meta.get('content'):
            metadata['generator'] = generator_meta.get('content')
        
        # Idioma
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            metadata['language'] = html_tag.get('lang')
        else:
            # Intentar detectar del contenido
            metadata['language'] = 'es'  # Asumiendo español por defecto
        
        # Archivo original
        metadata['source_file'] = str(file_path.relative_to(self.input_dir))
        metadata['processed_date'] = datetime.now().isoformat()
        
        return metadata
    
    def clean_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Limpiar HTML de elementos innecesarios (mejorado)
        
        Args:
            soup: Objeto BeautifulSoup
            
        Returns:
            Soup limpio
        """
        # Eliminar tags completos
        for tag_name in self.tags_to_remove:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Eliminar comentarios HTML
        from bs4 import Comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Eliminar imágenes decorativas (linea.gif, spacer.gif, etc.)
        for img in soup.find_all('img'):
            src = img.get('src', '').lower()
            if any(x in src for x in ['linea.gif', 'spacer.gif', 'pixel.gif', 'blank.gif']):
                img.decompose()
        
        # Eliminar atributos innecesarios
        for tag in soup.find_all(True):
            attrs_to_del = []
            for attr in list(tag.attrs.keys()):
                if attr.lower() in self.attrs_to_remove or \
                   attr.startswith('data-') or \
                   attr.startswith('aria-') or \
                   attr.startswith('on'):  # onclick, onload, etc.
                    attrs_to_del.append(attr)
            for attr in attrs_to_del:
                del tag[attr]
        
        # Limpiar divs y spans vacíos
        for tag in soup.find_all(['div', 'span', 'p', 'font', 'center']):
            if not tag.get_text(strip=True) and not tag.find('img'):
                tag.decompose()
        
        # Convertir <font> a texto simple (HTML legacy)
        for font_tag in soup.find_all('font'):
            font_tag.unwrap()
        
        return soup
    
    def extract_main_content(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Extraer contenido principal (mejorado para HTML legacy)
        
        Args:
            soup: Objeto BeautifulSoup
            
        Returns:
            Soup con contenido principal
        """
        # Buscar tags de contenido principal
        main_content = soup.find('main') or \
                      soup.find('article') or \
                      soup.find('div', class_=re.compile(r'content|main|article|body', re.I)) or \
                      soup.find('div', id=re.compile(r'content|main|article|body', re.I))
        
        if main_content:
            new_soup = BeautifulSoup('<html><body></body></html>', 'html.parser')
            new_soup.body.append(main_content)
            return new_soup
        
        # Si no encuentra, usar body completo (común en HTML legacy)
        body = soup.find('body')
        if body:
            return soup
        
        return soup
    
    def improve_tables(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Mejorar conversión de tablas a Markdown
        
        Args:
            soup: Objeto BeautifulSoup
            
        Returns:
            Soup con tablas mejoradas
        """
        for table in soup.find_all('table'):
            # Eliminar atributos de presentación
            for attr in ['width', 'border', 'cellpadding', 'cellspacing', 'bgcolor']:
                if table.get(attr):
                    del table[attr]
            
            # Limpiar celdas
            for cell in table.find_all(['td', 'th']):
                # Eliminar atributos de presentación
                for attr in ['width', 'bgcolor', 'align', 'valign']:
                    if cell.get(attr):
                        del cell[attr]
                
                # Convertir <h4> dentro de celdas a texto normal con énfasis
                for h4 in cell.find_all('h4'):
                    h4.name = 'strong'
        
        return soup
    
    def preserve_anchors(self, soup: BeautifulSoup) -> BeautifulSoup:
        """
        Preservar anclas internas como headers de Markdown
        
        Args:
            soup: Objeto BeautifulSoup
            
        Returns:
            Soup con anclas preservadas
        """
        for anchor in soup.find_all('a', attrs={'name': True}):
            name = anchor.get('name')
            # Si el ancla está seguida por un heading, agregar ID al heading
            next_sibling = anchor.find_next_sibling(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if next_sibling:
                # Markdown soporta IDs en headers: ## Header {#id}
                current_text = next_sibling.get_text()
                # Agregar el ancla como referencia en el texto
                next_sibling.string = f"{current_text} {{#{name}}}"
            # Eliminar el tag <a> ahora que preservamos el ancla
            anchor.decompose()
        
        return soup
    
    def format_metadata_header(self, metadata: Dict[str, str]) -> str:
        """
        Formatear metadata como encabezado YAML en Markdown
        
        Args:
            metadata: Diccionario de metadata
            
        Returns:
            String con metadata formateada
        """
        header = "---\n"
        for key, value in metadata.items():
            if isinstance(value, str):
                # Escapar comillas en valores
                value = value.replace('"', '\\"')
                header += f'{key}: "{value}"\n'
            else:
                header += f'{key}: {value}\n'
        header += "---\n\n"
        return header
    
    def clean_markdown(self, markdown_text: str) -> str:
        """
        Limpiar y mejorar el markdown generado
        
        Args:
            markdown_text: Texto en markdown
            
        Returns:
            Markdown limpio
        """
        # Eliminar múltiples líneas en blanco (más de 2 consecutivas)
        markdown_text = re.sub(r'\n{4,}', '\n\n\n', markdown_text)
        
        # Eliminar espacios al final de líneas
        markdown_text = re.sub(r' +\n', '\n', markdown_text)
        
        # Limpiar caracteres especiales problemáticos
        markdown_text = markdown_text.replace('\u200b', '')  # Zero-width space
        markdown_text = markdown_text.replace('\xa0', ' ')   # Non-breaking space
        markdown_text = markdown_text.replace('\r\n', '\n')  # Normalizar saltos
        
        # Mejorar formato de listas
        markdown_text = re.sub(r'\n(\s*)-\s+\n', r'\n\1- ', markdown_text)
        
        # Eliminar líneas que son solo puntos o espacios
        lines = markdown_text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and stripped != '.' and not all(c in '. ' for c in stripped):
                cleaned_lines.append(line)
            elif not stripped:  # Líneas vacías se mantienen
                cleaned_lines.append(line)
        
        markdown_text = '\n'.join(cleaned_lines)
        
        return markdown_text.strip()
    
    def convert_file(self, html_file: Path) -> Optional[Path]:
        """
        Convertir un archivo HTML a Markdown (versión mejorada)
        
        Args:
            html_file: Ruta del archivo HTML
            
        Returns:
            Ruta del archivo Markdown generado o None si falla
        """
        try:
            logger.info(f"Procesando: {html_file.relative_to(self.input_dir)}")
            
            # Leer archivo HTML con detección de encoding
            html_content = self.read_html_with_encoding(html_file)
            
            # Parsear HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extraer metadata ANTES de limpiar
            metadata = self.extract_metadata(soup, html_file)
            
            # Preservar anclas importantes
            soup = self.preserve_anchors(soup)
            
            # Extraer contenido principal
            soup = self.extract_main_content(soup)
            
            # Mejorar tablas
            soup = self.improve_tables(soup)
            
            # Limpiar HTML
            soup = self.clean_html(soup)
            
            # Convertir a Markdown
            markdown_content = self.h2t.handle(str(soup))
            
            # Limpiar markdown
            markdown_content = self.clean_markdown(markdown_content)
            
            # Verificar que hay contenido útil
            if len(markdown_content.strip()) < 50:
                logger.warning(f"Contenido muy corto en {html_file.name}, omitiendo...")
                self.stats['skipped'] += 1
                return None
            
            # Agregar metadata como encabezado
            final_content = self.format_metadata_header(metadata) + markdown_content
            
            # Determinar ruta de salida (preservar estructura de directorios)
            relative_path = html_file.relative_to(self.input_dir)
            output_file = self.output_dir / relative_path.with_suffix('.md')
            
            # Crear directorios si no existen
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Escribir archivo Markdown
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            self.stats['processed'] += 1
            self.stats['total_size'] += len(final_content)
            logger.info(f"✓ Convertido: {output_file.relative_to(self.output_dir)}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"Error procesando {html_file.name}: {e}")
            import traceback
            traceback.print_exc()
            self.stats['failed'] += 1
            return None
    
    def convert_directory(self) -> Dict[str, int]:
        """
        Convertir todos los archivos HTML en el directorio
        
        Returns:
            Estadísticas de conversión
        """
        if not self.input_dir.exists():
            logger.error(f"El directorio {self.input_dir} no existe")
            return self.stats
        
        # Crear directorio de salida
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Buscar archivos HTML recursivamente
        html_files = list(self.input_dir.rglob('*.html')) + \
                    list(self.input_dir.rglob('*.htm'))
        
        if not html_files:
            logger.warning(f"No se encontraron archivos HTML en {self.input_dir}")
            return self.stats
        
        logger.info(f"Encontrados {len(html_files)} archivos HTML")
        logger.info("=" * 60)
        
        # Procesar cada archivo
        for html_file in html_files:
            self.convert_file(html_file)
        
        # Mostrar estadísticas
        logger.info("\n" + "=" * 60)
        logger.info("ESTADÍSTICAS DE CONVERSIÓN")
        logger.info("=" * 60)
        logger.info(f"Archivos procesados:  {self.stats['processed']}")
        logger.info(f"Archivos omitidos:    {self.stats['skipped']}")
        logger.info(f"Archivos con error:   {self.stats['failed']}")
        logger.info(f"Problemas encoding:   {self.stats['encoding_issues']}")
        logger.info(f"Tamaño total (chars): {self.stats['total_size']:,}")
        logger.info("=" * 60)
        
        return self.stats


def main():
    """Función principal"""
    # Configuración
    INPUT_DIR = "html"
    OUTPUT_DIR = "md"
    
    # Crear conversor mejorado
    converter = ImprovedHTMLtoMarkdownConverter(INPUT_DIR, OUTPUT_DIR)
    
    # Ejecutar conversión
    stats = converter.convert_directory()
    
    # Verificar resultados
    if stats['processed'] > 0:
        logger.info(f"\n✓ Conversión completada exitosamente")
        logger.info(f"  Archivos Markdown generados en: {OUTPUT_DIR}/")
    else:
        logger.warning("\n⚠ No se procesaron archivos")


if __name__ == "__main__":
    main()