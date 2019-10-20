$(document).ready(function () {
    let map = L.map('map').setView([51.1876767, 4.4072676], 10);
    let layerGroup = L.layerGroup().addTo(map);
    let routing;

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // L.marker([51.1876767, 4.4072676]).addTo(map)
    //     .bindPopup('A pretty CSS3 popup.<br> Easily customizable.')
    //     .openPopup();

    map.on('moveend', function () {
        // console.log(map.getBounds());
    });

    // @http://www.liedman.net/leaflet-routing-machine/
    // L.Routing.control({
    //     waypoints: [
    //         L.latLng(57.74, 11.94),
    //         L.latLng(57.6792, 11.949)
    //     ]
    // }).addTo(map);

    $('select').on('change', function () {
        layerGroup.clearLayers();
        if (routing)
            map.removeControl(routing);
        let num = $('option:selected', this).attr('num');
        let entity = $('option:selected', this).attr('entity');
        $.ajax({
            url: "/api/stops/" + entity + "/" + num + "/FIND",
            // data: JSON.stringify({
            //     "id": $(this).attr('id').split('_')[1]
            // }),
            // type: 'GET',
            // dataType: 'json',
            // contentType: 'application/json',
            success: function (response) {
                let coords = []
                response["haltes"].forEach(halte => {
                    // console.log(halte)
                    coords.push(L.Routing.waypoint(L.latLng(halte.geoCoordinaat.latitude, halte.geoCoordinaat.longitude), halte.omschrijving));
                    // L.marker([halte.geoCoordinaat.latitude, halte.geoCoordinaat.longitude]).addTo(layerGroup)
                    //     .bindPopup(halte.omschrijving);
                });
                routing = L.Routing.control({ "waypoints": coords }).addTo(map);
            },
            error: function (error) {
                console.log(error);
            }
        })
    });

});