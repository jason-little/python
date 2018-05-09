import folium
map = folium.Map(location=[38.58, -99.09], zoom_start=6, tiles="Mapbox Bright")
fg = folium.FeatureGroup(name="MyMap")
fg.add_child(folium.Marker(location=[38.2, -99.1], popup="Hi I am a marker", icon=folium.Icon(color='green')))
fg.add_child(folium.Marker(location=[37.2, -97.1], popup="Hi I am a marker", icon=folium.Icon(color='blue')))
map.add_child(fg)


#fine for adding one child but instead use feature groups above
#map.add_child(folium.Marker(location=[38.2, -99.1], popup="Hi I am a marker", icon=folium.Icon(color='green')))
map.save("Map1.html")
