let stopsLayer;
let busLayer;
let stopIcon;
let busIcon;

function load() {
    $("#spinspin").show();
    let num = $("option:selected", this).attr("num");
    let entity = $("option:selected", this).attr("entity");
    let direction = $("option:selected", this).attr("direction");
    document.getElementById("line-info").innerHTML = `<h3>${num} ${entity} ${direction}</h3>`;
    $.ajax({
        url: `/api/real-time/${entity}/${num}/${direction}`,
        success: function (response) {
            $("#spinspin").hide();
            stopsLayer.clearLayers();
            busLayer.clearLayers();
            response["haltes"].forEach(halte => {
                let haltemarker = L.marker([halte.geoCoordinaat.latitude, halte.geoCoordinaat.longitude], {icon: stopIcon, entity: halte.entiteitnummer, haltenr: halte.haltenummer}).addTo(stopsLayer)
                    .bindPopup(`Halte: ${halte.omschrijving}`);
                haltemarker.on("click", onClick);
            });
            response["busses"].forEach(bus => {
                L.marker([bus.geoCoordinaat.latitude, bus.geoCoordinaat.longitude], {icon: busIcon}).addTo(busLayer)
                    .bindPopup(`Bus: ${bus.ritnummer}`);
            });
        },
        error: function (error) {
            $("#spinspin").hide();
            console.log(error);
        }
    });
}

function onClick(e) {
    let hentity = e.target.options.entity;
    let hnum = e.target.options.haltenr;
    $.ajax({
        url: `/api/halte/${hentity}/${hnum}`,
        success: function (response) {
            document.getElementById("stop-info").innerHTML = 
            `<h3> ${response.omschrijving} </h3>
            <img src="http://openweathermap.org/img/wn/${response.weather.weather[0].icon}@2x.png">
            <h6> ${response.weather.weather[0].main}: ${response.weather.weather[0].description} </h6>
            <h6> Temperature: ${(response.weather.main.temp - 273).toFixed(2)}°C </h6>
            `;
        },
        error: function (error) {
            console.log(error);
        }
    });
}

$(document).ready(function () {
    let map = L.map("map").setView([51.1876767, 4.4072676], 10);
    stopsLayer = L.layerGroup().addTo(map);
    busLayer = L.layerGroup().addTo(map);

    L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    stopIcon = new L.Icon({
        iconUrl: "/static/bus-stop.png",
        iconSize: [32, 32]
    });

    busIcon = new L.Icon({
        iconUrl: "/static/bus.png",
        iconSize: [40, 40]
    });

    // L.marker([51.1876767, 4.4072676]).addTo(map)
    //     .bindPopup("A pretty CSS3 popup.<br> Easily customizable.")
    //     .openPopup();

    // map.on("moveend", function () {
    //     // console.log(map.getBounds());
    // });

    // @http://www.liedman.net/leaflet-routing-machine/
    // L.Routing.control({
    //     waypoints: [
    //         L.latLng(57.74, 11.94),
    //         L.latLng(57.6792, 11.949)
    //     ]
    // }).addTo(map);

    $("select").on("change", load);
    $("select").on("loaded.bs.select", load);

    $("#bus-reload").on("click", function() {
        let num = $("#select-line :selected").attr("num");
        let entity = $("#select-line :selected").attr("entity");
        let direction = $("#select-line :selected").attr("direction");
        $.ajax({
            url: `/api/update/${entity}/${num}/${direction}`,
            success: function (response) {
                busLayer.clearLayers();
                response["busses"].forEach(bus => {
                    L.marker([bus.geoCoordinaat.latitude, bus.geoCoordinaat.longitude], {icon: busIcon}).addTo(busLayer)
                        .bindPopup(`Bus: ${bus.ritnummer}`);
                });
            },
            error: function (error) {
                console.log(error);
            }
        });
    });
});
