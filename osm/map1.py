import folium
import pandas

data = pandas.read_csv("Volcanoes.txt")
lat = list(data["LAT"])
lon = list(data["LON"])
name = list(data["NAME"])
elev = list(data["ELEV"])

# color based on elevation
def color_producer(elevation):
    if elevation < 1000:
        return 'green'
    elif 1000 <= elevation < 3000:
        return 'orange'
    else:
        return 'red'

map = folium.Map(location=[38.58, -99.09], zoom_start=6, tiles="Mapbox Bright")

fg = folium.FeatureGroup(name="MyMap")

for lt, ln, el in zip(lat, lon, elev):
    fg.add_child(folium.CircleMarker(location=[lt, ln], radius=6, popup=folium.Popup(str(el)+" m", parse_html=True), fill_color=color_producer(el), color = 'grey', fill = True, fill_opacity=0.7))

fg.add_child(folium.GeoJson(open('world.json', encoding = "utf-8-sig").read()))

map.add_child(fg)

#doing it by name to solve the case of an apostrophy
#for lt, ln, nm in zip(lat, lon, name):
#    fg.add_child(folium.Marker(location=[lt, ln], popup=folium.Popup(str(nm), parse_html=True), icon=folium.Icon(color='green')))
#map.add_child(fg)
#fine for adding one child but instead use feature groups above
#map.add_child(folium.Marker(location=[38.2, -99.1], popup="Hi I am a marker", icon=folium.Icon(color='green')))
map.save("Map1.html")
