
odoo.define('client.client', function (require){
    "use strict";
    var ajax = require('web.ajax');
    var FormController = require('web.FormController');
     var rpc = require('web.rpc');

    //Content Link URL
    var iframe_src = '';


    FormController.include({

        //For Surveyed Plots
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
                    console.log(data);
                    //file_no = data.file_no;  
                    iframe_src = "http://localhost/mm/trial.php?file_no=" + file_no;
                    //alert('View Surveyed Plot....');
                    $('#clientmap_iframe').attr('src', iframe_src);
                });
                
            }

            return res;
        },


        //For Locate Quary
        _onButtonClicked: function (event) {
            if(event.data.attrs.name === "compute_lo"){
                var self = this;   
                var coordinate_x = $("input[name='coordinate_x']").val(); 
                var coordinate_y = $("input[name='coordinate_y']").val(); 
                //var coordinate_x = this.field_manager.get_field_value('coordinate_x');
                //var coordinate_y = this.field_manager.get_field_value('coordinate_y');  
                //Send Coordinates to Iframe-src
                iframe_src = "http://localhost/mm/p.php?coord_x=" + coordinate_x + "&coord_y=" + coordinate_y
                //Load Iframe src 
                //alert('Loading Content ....');
                document.getElementById("locatequery_iframe").src = iframe_src;      

                return;
            }
            this._super(event);
        },


         //For Locate Quary
        _onButtonClicked: function (event) {
            if(event.data.attrs.name === "action_check_points"){
                //Sample Parameter -- does nothing actually
                //sample_param = ''  -  {'sample_param':sample_param}
                //RPC Method
                rpc.query({
                    model: 'client.client',
                    method: 'action_check_points',
                    args: [],
                }).then(function (data) { 
                    console.log(data);
                    //file_no = data.file_no;  
                    iframe_src = "http://localhost/mm/trial.php?file_no=" + data;
                    //alert('View Surveyed Plot....');
                    $('#plotcoordinates_iframe').attr('src', iframe_src);
                });
                


                //Send Coordinates to Iframe-src
                iframe_src = "http://localhost/mm/p.php?coord_x=" + coordinate_x + "&coord_y=" + coordinate_y
                //Load Iframe src 
                //alert('Loading Content ....');
                document.getElementById("locatequery_iframe").src = iframe_src;      

                return;
            }
            //this._super(event);
        },


        
        GetEl: function (widgets, fieldName) {
            return _.findWhere(widgets, {name: fieldName});
        },
    });

});

console.log('Loaded customjs.js');



