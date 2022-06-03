const { createApp, ref, toRaw } = Vue

var terrain_basemap = L.tileLayer('https://stamen-tiles-{s}.a.ssl.fastly.net/terrain-background/{z}/{x}/{y}{r}.{ext}', {
	attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
	subdomains: 'abcd',
	minZoom: 0,
	maxZoom: 18,
	ext: 'png'
});

var osm_basemap = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
	maxZoom: 19,
	attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
});

var Lmap = null;
var Lmarkers = null

var vuem = createApp({
    data() { return {
        current_basemap: "osm",
        localities: null,
        current_locality: false,
    }},
    methods: {
        async onSwitchBasemap(e) {
            const vm = this;
            if (vm.current_basemap == "terrain") {
                Lmap.removeLayer(terrain_basemap);
                osm_basemap.addTo(Lmap);
                vm.current_basemap = "osm";
            } else {
                Lmap.removeLayer(osm_basemap);
                terrain_basemap.addTo(Lmap);
                vm.current_basemap = "terrain";
            }
        },
        async onFullMap(e) {
            const vm = this;
            $('#mapdiv').css({height: "90%", "display": "block"});
            $('#maintable').css({"max-height": "10%"});
            setTimeout(function(){ Lmap.invalidateSize()}, 200);
        },
        async onHalfMap(e) {
            const vm = this;
            $('#mapdiv').css({height: "60%", "display": "block"});
            $('#maintable').css({"max-height": "40%"});
            setTimeout(function(){ Lmap.invalidateSize()}, 200);
        },
        async onNoMap(e) {
            $('#mapdiv').css({display: "none"})
            $('#maintable').css({"max-height": "100%"});
        },
    },
    mounted: function () {
        var vm = this;
        this.$nextTick(function() {
            fetch("localities.json")
            .then(response => response.json())
            .then(json => {
                vm.localities = json;
                Lmap = L.map('mapdiv').setView([0, 0], 1);
                osm_basemap.addTo(Lmap);
                Lmarkers = L.markerClusterGroup();


                Object.values(vm.localities)
                .forEach(function(p) {
                    var marker = L.marker([p.lat, p.lon])
                        .on('click', function (e) {
                            vm.current_locality = p.locality_name;
                            $('#mapdiv').css({height: "60%", "display": "block"});
                            $('#maintable').css({"max-height": "40%"});
                            setTimeout(function(){ Lmap.invalidateSize()}, 200);
                        })
                       .bindTooltip(p.locality_name, { permanent: true, direction: 'right' });
                    Lmarkers.addLayer(marker);
                });

                Lmap.addLayer(Lmarkers);
                Lmap.fitBounds(Lmarkers.getBounds());
            })
            .catch(error => console.log(error));
        });
    }
}).mount("#mapapp");

__EXTRA_JS__
