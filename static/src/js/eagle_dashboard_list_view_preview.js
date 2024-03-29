eagle.define('eagle_dashboard_list.eagle_dashboard_list_view_preview', function (require) {
    "use strict";

    var registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');

    var QWeb = core.qweb;
    var field_utils = require('web.field_utils');

    var KsListViewPreview = AbstractField.extend({
        supportedFieldTypes: ['char'],

        resetOnAnyFieldChange: true,

        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.state = {};
        },

        _render: function () {
            this.$el.empty()
            var rec = this.recordData;
            if (rec.eagle_dashboard_item_type === 'eagle_list_view') {
                if(rec.eagle_list_view_type=="ungrouped"){
                    if (rec.eagle_list_view_fields.count !== 0) {
                        this.ksRenderListView();
                    } else {
                        this.$el.append($('<div>').text("Select Fields to show in list view."));

                    }
                }else if(rec.eagle_list_view_type=="grouped"){
                    if (rec.eagle_list_view_group_fields.count !== 0 && rec.eagle_chart_relation_groupby ) {
                        if(rec.eagle_chart_groupby_type ==='relational_type' || rec.eagle_chart_groupby_type ==='selection' || rec.eagle_chart_groupby_type ==='other'  || rec.eagle_chart_groupby_type ==='date_type' && rec.eagle_chart_date_groupby){
                            this.ksRenderListView();
                        }else{
                            this.$el.append($('<div>').text("Select Group by Date to show list data."));
                        }

                    } else {
                        this.$el.append($('<div>').text("Select Fields and Group By to show in list view."));

                    }
                }

            }
        },

        ksRenderListView: function () {
            var field = this.recordData;
            var eagle_list_view_name;
            var list_view_data = JSON.parse(field.eagle_list_view_data);
            if (field.name) eagle_list_view_name = field.name;
            else if (field.eagle_model_name) eagle_list_view_name = field.eagle_model_id.data.display_name;
            else eagle_list_view_name = "Name";
            if( field.eagle_list_view_type === "ungrouped" && list_view_data){
                var index_data = list_view_data.date_index;
                for (var i = 0; i < index_data.length; i++){
                    for (var j = 0; j < list_view_data.data_rows.length; j++){
                        var index = index_data[i]
                        var date = list_view_data.data_rows[j]["data"][index]
                        if (date) list_view_data.data_rows[j]["data"][index] = field_utils.format.datetime(moment(moment(date).utc(true)._d), {}, {timezone: false});
                        else list_view_data.data_rows[j]["data"][index] = "";
                    }
                }
            }

            if (field.eagle_list_view_data){
                var data_rows = list_view_data.data_rows;
                for (var i = 0; i < list_view_data.data_rows.length; i++){
                    for (var j = 0; j < list_view_data.data_rows[0]["data"].length; j++){
                        if(typeof(list_view_data.data_rows[i].data[j]) === "number" || list_view_data.data_rows[i].data[j]){
                            if(typeof(list_view_data.data_rows[i].data[j]) === "number"){
                                list_view_data.data_rows[i].data[j]  = field_utils.format.float(list_view_data.data_rows[i].data[j], Float64Array)
                            }
                        } else {
                            list_view_data.data_rows[i].data[j] = "";
                        }
                    }
                }
            }
            else list_view_data = false;

            var $listViewContainer = $(QWeb.render('eagle_list_view_container', {
                eagle_list_view_name: eagle_list_view_name,
                list_view_data: list_view_data
            }));
            this.$el.append($listViewContainer);

        },

    });
    registry.add('eagle_dashboard_list_view_preview', KsListViewPreview);

    return {
        KsListViewPreview: KsListViewPreview,
    };

});