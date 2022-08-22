
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
                    console.log(data);
                    //file_no = data.file_no;  
                    iframe_src = "http://192.168.1.8:8080/mm/trial.php?file_no=" + file_no;
                    //alert('View Surveyed Plot....');
                    $('#clientmap_iframe').attr('src', iframe_src);
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



