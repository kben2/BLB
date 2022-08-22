//Renders the maps of the locate query.
odoo.define('client.locate_query', function (require){
    "use strict";
    var ajax = require('web.ajax');
    var FormController = require('web.FormController');
    var rpc = require('web.rpc');
    var Widget = require('web.Widget');
    var FormView = require('web.FormView');


    //Content Link URL
    var iframe_src = '';

    FormController.include({
        _onButtonClicked: function (event) {
            if(event.data.attrs.name === "compute_map"){
                var self = this;   
                var coordinate_x = $("input[name='coordinate_x']").val(); 
                var coordinate_y = $("input[name='coordinate_y']").val(); 
                //var coordinate_x = this.field_manager.get_field_value('coordinate_x');
                //var coordinate_y = this.field_manager.get_field_value('coordinate_y');  
                //Send Coordinates to Iframe-src
                iframe_src = "http://192.168.1.8:8080/mm/p.php?coord_x=" + coordinate_x + "&coord_y=" + coordinate_y
                //Load Iframe src 
                //alert('Loading Content ....');
                document.getElementById("locatequery_iframe").src = iframe_src;      

                return;
            }
            this._super(event);
        },
    });


});

console.log('Loaded Custom-Dashboard.js');

odoo.define('client.client', function (require){
    "use strict";
    var ajax = require('web.ajax');
    var FormController = require('web.FormController');
     var rpc = require('web.rpc');

    //Content Link URL
    var iframe_src = '';


    FormController.include({
        _update: function () {
            var res = this._super.apply(this, arguments);
            
            if (this.modelName === 'client.client') {
                //// Get some available variables:
                var data = this.renderer.state.data;
                var fields = this.renderer.state.fields;
                var context = this.renderer.state.context;
                var fieldsInfo = this.renderer.state.fieldsInfo.form;
                var fieldWidgets = this.renderer.allFieldWidgets[this.renderer.state.id];
                
                //// Debug:
                console.log('data ==', data);
                console.log('fields ==', fields);
                console.log('context ==', context);
                console.log('fieldsInfo ==', fieldsInfo);
                console.log('fieldWidgets ==', fieldWidgets);

                var file_no = data.file_no;
                console.log('file_no ==', file_no); 

                //RPC Method
                rpc.query({
                    model: 'client.client',
                    method: 'get_clientmap',
                    args: [{'file_no':file_no}],
                }).then(function (data) { 
                    // console.log(data);
                    //file_no = data.file_no;  
                    iframe_src = "http://192.168.1.8:8080/mm/trial.php?file_no=" + file_no;
                    //alert('View Surveyed Plot....');
                    $('#clientmap_iframe').attr('src', iframe_src);
                }).fail(function (){
        console.error('Failed');
              });
                
            }

            return res;
        },
        
        GetEl: function (widgets, fieldName) {
            return _.findWhere(widgets, {name: fieldName});
        },
    });

});

console.log('Loaded customjs.js');
//Renders plot coordinates during file opening as a map
odoo.define('client.client', function (require){
    "use strict";
    var ajax = require('web.ajax');
    var FormController = require('web.FormController');
     var rpc = require('web.rpc');

    //Content Link URL
    var iframe_src = '';


    FormController.include({
        _update: function () {
            var res = this._super.apply(this, arguments);
            
            if (this.modelName === 'client.client') {
                //// Get some available variables:
                var data = this.renderer.state.data;
                var fields = this.renderer.state.fields;
                var context = this.renderer.state.context;
                var fieldsInfo = this.renderer.state.fieldsInfo.form;
                var fieldWidgets = this.renderer.allFieldWidgets[this.renderer.state.id];
                
                //// Debug:
                console.log('data ==', data);
                console.log('fields ==', fields);
                console.log('context ==', context);
                console.log('fieldsInfo ==', fieldsInfo);
                console.log('fieldWidgets ==', fieldWidgets);

                // var plot_coordinates = data.plot_coordinates.data[0]['data']['coordinate_x'];
                // var coordinate_x = $("input[name='plot_geojson']").val();
                // console.log('coordinate_x ==', coordinate_x); 
                var geo = data.plot_geojson;
                var x = data.centroid_eastings;
                var y = data.centroid_northings;
                iframe_src = "http://192.168.1.8:8080/mm/estimate.php?geo=" + geo + "&x=" + x + "&y=" + y;
                    //alert(iframe_src);
                    $('#plotcoordinates_iframe').attr('src', iframe_src);
              
        // //         //RPC Method
        //         rpc.query({
        //             model: 'client.client',
        //             method: 'compute_area_estimate',
        //             args: [{}],
        //         }).then(function (data) { 
        //             console.log(y);
        //             //alert(y);
        //             //stringdata = data;  
        //             iframe_src = "http://localhost/mm/estimate.php?geo=" + geo + "&x=" + x + "&y=" + y;
        //             //alert(iframe_src);
        //             $('#plotcoordinates_iframe').attr('src', iframe_src);
        //         }).fail(function (){
        // console.error('Failed');
        //         });
                
            }

            return res;
        },
        
        GetEl: function (widgets, fieldName) {
            return _.findWhere(widgets, {name: fieldName});
        },
    });

});

console.log('Loaded customjs.js');

// odoo.define('client.locate_query', function (require){
//     "use strict";
//     var ajax = require('web.ajax');
//     var FormController = require('web.FormController');
//      var rpc = require('web.rpc');

//     //Content Link URL
//     var iframe_src = '';


//     FormController.include({
//         _update: function () {
//             var res = this._super.apply(this, arguments);
            
//             if (this.modelName === 'client.locate_query') {
//                 //// Get some available variables:
//                 var data = this.renderer.state.data;
//                 var fields = this.renderer.state.fields;
//                 var context = this.renderer.state.context;
//                 var fieldsInfo = this.renderer.state.fieldsInfo.form;
//                 var fieldWidgets = this.renderer.allFieldWidgets[this.renderer.state.id];
                
//                 //// Debug:
//                 console.log('data ==', data);
//                 console.log('fields ==', fields);
//                 console.log('context ==', context);
//                 console.log('fieldsInfo ==', fieldsInfo);
//                 console.log('fieldWidgets ==', fieldWidgets);

//                 var x = data.coordinate_x;
//                 var y = data.coordinate_y;
//                 console.log(x);
//                 //Send Coordinates to Iframe-src
//                 iframe_src = "http://localhost/mm/p.php?coord_x=" + x + "&coord_y=" + y
//                 //Load Iframe src 
//                 //alert('Loading Content ....');
//                 document.getElementById("locatequery_iframe").src = iframe_src;
//                 // var plot_coordinates = data.plot_coordinates.data[0]['data']['coordinate_x'];
//                 // var coordinate_x = $("input[name='plot_geojson']").val();
//                 // console.log('coordinate_x ==', coordinate_x); 
//                 // var geo = data.plot_geojson;
//                 // var x = data.centroid_eastings;
//                 // var y = data.centroid_northings;
//                 // iframe_src = "http://localhost/mm/estimate.php?geo=" + geo + "&x=" + x + "&y=" + y;
//                 //     //alert(iframe_src);
//                 //     $('#plotcoordinates_iframe').attr('src', iframe_src);
              
//         // //         //RPC Method
//         //         rpc.query({
//         //             model: 'client.client',
//         //             method: 'compute_area_estimate',
//         //             args: [{}],
//         //         }).then(function (data) { 
//         //             console.log(y);
//         //             //alert(y);
//         //             //stringdata = data;  
//         //             iframe_src = "http://localhost/mm/estimate.php?geo=" + geo + "&x=" + x + "&y=" + y;
//         //             //alert(iframe_src);
//         //             $('#plotcoordinates_iframe').attr('src', iframe_src);
//         //         }).fail(function (){
//         // console.error('Failed');
//         //         });
                
//             }

//             return res;
//         },
        
//         GetEl: function (widgets, fieldName) {
//             return _.findWhere(widgets, {name: fieldName});
//         },
//     });

// });

// console.log('Loaded customjs2.js');

