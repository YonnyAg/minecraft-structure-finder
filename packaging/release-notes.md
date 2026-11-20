Primera versión portable de **Minecraft Structure Finder** para **Windows x64**.

### Descargar y abrir

1. Descarga **MinecraftStructureFinder-v1.0.0-windows-x64.zip** en Assets.
2. Extrae todo el ZIP.
3. Abre **MinecraftStructureFinder.exe** con doble clic.

No necesitas instalar Python, abrir una consola ni instalar mods. Conserva la carpeta `_internal` junto al ejecutable. Los archivos **Source code** son para desarrollo.

### Incluye

- Búsqueda de cabañas de brujas para Minecraft Java 26.3: la más cercana o todas en un área.
- Agrupaciones con cantidad mínima y radio común, coordenadas y copia de resultados.
- Perímetro horizontal por chunks, límites de coordenadas y cancelación de búsquedas.
- Motor Cubiomes y dependencias incluidas; las búsquedas funcionan sin conexión.

Los centros y perímetros son referencias geométricas; no certifican un punto AFK ni producción máxima. Esta versión no incluye otras estructuras, Bedrock o lectura de mundos.

Se verificó con 22 pruebas automatizadas y una comprobación del ejecutable extraído del ZIP, con Python fuera de PATH: búsqueda real, 24 cabañas del ejemplo, tres grupos, perímetro, portapapeles y cancelación.

El archivo `.sha256` permite comprobar la integridad del ZIP. El paquete incluye los avisos de licencia de sus componentes.
