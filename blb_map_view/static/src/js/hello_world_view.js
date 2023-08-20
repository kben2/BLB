odoo.define('hello_world_view.HelloWorldView', function (require) {
"use strict";


var AbstractController = require('web.AbstractController');
var AbstractModel = require('web.AbstractModel');
var AbstractRenderer = require('web.AbstractRenderer');
var AbstractView = require('web.AbstractView');
var viewRegistry = require('web.view_registry');


var HelloWorldController = AbstractController.extend({});
var HelloWorldRenderer = AbstractRenderer.extend({
    className: "o_hello_world_view",
    on_attach_callback: function () {
        this.isInDOM = true;
        this._renderMap();
    },
    _render: function () {
            if (this.isInDOM) {
                this._renderMarkers();
                return $.when();
            }
            this.$el.append(
                $('<div>').append(
                    $('<input>').attr('type', 'text').attr('id', 'x-coord').attr('style', 'width: 200px; margin-bottom: 10px;margin-top: 10px;margin-left: 10px;').attr('placeholder', 'X Position'),
                    $('<input>').attr('type', 'text').attr('id', 'y-coord').attr('style', 'width: 200px; margin-bottom: 10px;margin-top: 10px;margin-left: 10px;').attr('placeholder', 'Y Position'),
                    $('<div class="btn-group" role="toolbar" aria-label="Main actions">')
                        .append(
                            $('<button class="btn btn-primary">').attr('style', 'margin-bottom: 10px;margin-top: 10px;margin-left: 10px;').text('Add your location').on('click', this._onAddMarkerClick.bind(this))
                        ),
                    $('<div>').attr('id', 'mapid')

                )
            );
            return $.when();
        },
/*	_render: function () {
        if (this.isInDOM) {
            this._renderMarkers();
            return $.when();
        }
    	this.$el.append(
                // $('<h1>').text('GIS Maps!'),
                $('<div id="mapid"/>')
        );
        return $.when();
	},*/
    _renderMap: function () {
        if (!this.map) {
            this.map = L.map('mapid').setView([0.309010, 32.5578232], 17);
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        maxZoom: 18,
                        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        }).addTo(this.map);
        }
        this._renderMarkers();
    },
    _renderMarkers: function () {
        var self = this;

        if (this.markers) this.markers.map(function (marker) {marker.removeFrom(self.map);});
        this.markers = [];

/*        var marker = L.marker([0.309010, 32.557823]).addTo(this.map);
        marker.bindPopup("<b>Web GIS loading!</b>").openPopup();
        this.markers.push(marker);*/

        this.state.contacts.forEach(function (contact) {
            self.markers.push(
                L.marker(
                    [contact.latitude, contact.longitude],
                    {title: contact.name, contact_id: contact.id}
                )
                .addTo(self.map)
                .on('click', self._onContactMarkerClick.bind(self)));
        });
    },
    _onAddMarkerClick: function () {
        var x = parseFloat($('#x-coord').val());
        var y = parseFloat($('#y-coord').val());
        if (!isNaN(x) && !isNaN(y)) {
            var marker = L.marker([x, y]).addTo(this.map);
            this.markers.push(marker);
        }
    },
    _onContactMarkerClick: function (event) {
        var action = {
            type: 'ir.actions.act_window',
            views: [[false, 'form']],
            res_model: 'client.locate_query',
            res_id: event.target.options.contact_id,
        };
        this.do_action(action);
    }

});
var HelloWorldModel = AbstractModel.extend({
    get: function () {
        return {contacts: this.contacts};
    },
    load: function (params) {
        this.displayContacts = params.displayContacts  ? true : false;
        return this._load(params);
    },
    reload: function (id, params) {
        return this._load(params);
    },
    _load: function (params) {
        this.domain = params.domain || this.domain || [];
        if (this.displayContacts) {
            var self = this;
            return this._rpc({
                model: 'client.locate_query',
                method: 'search_read',
                fields: ['id','name','latitude', 'longitude'],
                domain: this.domain,
            })
            .then(function (result) {
                self.contacts = result;
            });
        }
        this.contacts = [];
        return $.when();
    },
});

var HelloWorldView = AbstractView.extend({
    config: _.extend({}, AbstractView.prototype.config, {
        Model: HelloWorldModel,
        Controller: HelloWorldController,
        Renderer: HelloWorldRenderer,
    }),
    cssLibs: [
        '/hello_world_view/static/lib/leaflet/leaflet.css'
    ],
    jsLibs: [
        '/hello_world_view/static/lib/leaflet/leaflet.js',
    ],
    viewType: 'hello_world',
    groupable: false,

    init: function () {
        this._super.apply(this, arguments);
        this.loadParams.displayContacts = this.arch.attrs.display_contacts;
    },
});

viewRegistry.add('hello_world', HelloWorldView);

return HelloWorldView;

});


odoo.define('hello_world_view.HelloWorldController', function (require) {
"use strict";


var AbstractController = require('web.AbstractController');

var HelloWorldController = AbstractController.extend({});

return HelloWorldController;

});

odoo.define('hello_world_view.HelloWorldViewEvolution', function (require) {
"use strict";

var HelloWorldView = require('hello_world_view.HelloWorldView');
var HelloWorldController = require('hello_world_view.HelloWorldController');
var viewRegistry = require('web.view_registry');

var HelloWorldEvolutionController = HelloWorldController.extend({

    renderButtons: function ($node) {
        this.$buttons = $('<div>');
        var $button = $('<div class="btn-group" role="toolbar" aria-label="Main actions">')
                        .append(
                            $('<button class="btn btn-primary">').text('Toggle Contact Markers')
                        );
        $button.click(this._onButtonClick.bind(this));
        this.$buttons.append($button);
        this.$buttons.appendTo($node);
    },

    _onButtonClick: function (event) {
        this.model.displayContacts = !this.model.displayContacts;
        this.update({});
    },
});

var HelloWorldViewEvolution = HelloWorldView.extend({
    config: _.extend({}, HelloWorldView.prototype.config, {Controller: HelloWorldEvolutionController}) ,
});

viewRegistry.add('hello_world_evolution', HelloWorldViewEvolution);

return HelloWorldViewEvolution;

});
