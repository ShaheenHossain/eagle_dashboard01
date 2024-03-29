eagle.define('eagle_dashboard_list.eagle_dashboard_item_preview', function (require) {
    "use strict";

    var registry = require('web.field_registry');
    var AbstractField = require('web.AbstractField');
    var core = require('web.core');
    var field_utils = require('web.field_utils');
    var session = require('web.session');
    var utils = require('web.utils');

    var QWeb = core.qweb;

    var KsItemPreview = AbstractField.extend({

        supportedFieldTypes: ['integer'],

        file_type_magic_word: {
            '/': 'jpg',
            'R': 'gif',
            'i': 'png',
            'P': 'svg+xml',
        },

        //        Number Formatter into shorthand function
        ksNumFormatter: function (num, digits) {
            var negative;
            var si = [{
                    value: 1,
                    symbol: ""
                },
                {
                    value: 1E3,
                    symbol: "k"
                },
                {
                    value: 1E6,
                    symbol: "M"
                },
                {
                    value: 1E9,
                    symbol: "G"
                },
                {
                    value: 1E12,
                    symbol: "T"
                },
                {
                    value: 1E15,
                    symbol: "P"
                },
                {
                    value: 1E18,
                    symbol: "E"
                }
            ];
            if(num<0){
                num = Math.abs(num)
                negative = true
            }
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length - 1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }
            if(negative){
                return "-" +(num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            }else{
                return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            }
        },

        eagle_get_dark_color: function (color, opacity, percent) { // deprecated. See below.
            var num = parseInt(color.slice(1), 16),
                amt = Math.round(2.55 * percent),
                R = (num >> 16) + amt,
                G = (num >> 8 & 0x00FF) + amt,
                B = (num & 0x0000FF) + amt;
            return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 + (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 + (B < 255 ? B < 1 ? 0 : B : 255)).toString(16).slice(1) + "," + opacity;
        },

        _render: function () {
            var self = this;
            var field = self.recordData;
            var $val;
            var item_info;
            var eagle_rgba_background_color, eagle_rgba_font_color, eagle_rgba_icon_color;
            self.$el.empty();
            eagle_rgba_background_color = self._get_rgba_format(field.eagle_background_color)
            eagle_rgba_font_color = self._get_rgba_format(field.eagle_font_color)
            eagle_rgba_icon_color = self._get_rgba_format(field.eagle_default_icon_color)
            item_info = {
                name: field.name,
                //                    count: self.record.specialData.eagle_domain.nbRecords.toLocaleString('en', {useGrouping:true}),
                count: self.ksNumFormatter(field.eagle_record_count, 1),
                icon_select: field.eagle_icon_select,
                default_icon: field.eagle_default_icon,
                icon_color: eagle_rgba_icon_color,
            }
            if (field.eagle_icon) {

                if (!utils.is_bin_size(field.eagle_icon)) {
                    // Use magic-word technique for detecting image type
                    item_info['img_src'] = 'data:image/' + (self.file_type_magic_word[field.eagle_icon[0]] || 'png') + ';base64,' + field.eagle_icon;
                } else {
                    item_info['img_src'] = session.url('/web/image', {
                        model: self.model,
                        id: JSON.stringify(self.res_id),
                        field: "eagle_icon",
                        // unique forces a reload of the image when the record has been updated
                        unique: field_utils.format.datetime(self.recordData.__last_update).replace(/[^0-9]/g, ''),
                    });
                }

            }
            if (!field.name) {
                if (field.eagle_model_name) {
                    item_info['name'] = field.eagle_model_id.data.display_name;
                } else {
                    item_info['name'] = "Name";
                }
            }



            switch (field.eagle_layout) {
                case 'layout1':
                    $val = $(QWeb.render('eagle_db_list_preview_layout1', item_info));
                        $val.css({
                        "background-color": eagle_rgba_background_color,
                        "color": eagle_rgba_font_color
                    });
                    break;

                case 'layout2':
                    $val = $(QWeb.render('eagle_db_list_preview_layout2', item_info));
                    var eagle_rgba_dark_background_color_l2 = self._get_rgba_format(self.eagle_get_dark_color(field.eagle_background_color.split(',')[0], field.eagle_background_color.split(',')[1], -10));
                    $val.find('.eagle_dashboard_icon_l2').css({
                        "background-color": eagle_rgba_dark_background_color_l2,
                    });
                    $val.css({
                        "background-color": eagle_rgba_background_color,
                        "color": eagle_rgba_font_color
                    });
                    break;

                case 'layout3':
                    $val = $(QWeb.render('eagle_db_list_preview_layout3', item_info));
                    $val.css({
                        "background-color": eagle_rgba_background_color,
                        "color": eagle_rgba_font_color
                    });
                    break;

                case 'layout4':
                    $val = $(QWeb.render('eagle_db_list_preview_layout4', item_info));
                    $val.find('.eagle_dashboard_icon_l4').css({
                        "background-color": eagle_rgba_background_color,
                    });
                    $val.find('.eagle_dashboard_item_preview_customize').css({
                        "color": eagle_rgba_background_color,
                    });
                    $val.find('.eagle_dashboard_item_preview_delete').css({
                        "color": eagle_rgba_background_color,
                    });
                    $val.css({
                        "border-color": eagle_rgba_background_color,
                        "color": eagle_rgba_font_color
                    });
                    break;

                case 'layout5':
                    $val = $(QWeb.render('eagle_db_list_preview_layout5', item_info));
                    $val.css({
                        "background-color": eagle_rgba_background_color,
                        "color": eagle_rgba_font_color
                    });
                    break;

                case 'layout6':
                    //                        item_info['icon_color'] = self._get_rgba_format(self.eagle_get_dark_color(field.eagle_background_color.split(',')[0],field.eagle_background_color.split(',')[1],-10));
                    $val = $(QWeb.render('eagle_db_list_preview_layout6', item_info));
                    $val.css({
                        "background-color": eagle_rgba_background_color,
                        "color": eagle_rgba_font_color
                    });

                    break;

                default:
                    $val = $(QWeb.render('eagle_db_list_preview'));
                    break;

            }

            self.$el.append($val);
            self.$el.append(QWeb.render('eagle_db_item_preview_footer_note'));
        },


        _renderReadonly: function ($val) {
            var self = this;
            var eagle_icon_url;
            this._rpc({
                model: 'eagle_dashboard.item',
                method: 'eagle_set_preview_image',
                args: [self.res_id],
            }).then(function (data) {
                eagle_icon_url = 'data:image/' + (self.file_type_magic_word[data[0]] || 'png') + ';base64,' + data;
                $val.find('.eagle_db_list_image').attr('src', eagle_icon_url)
                self.$el.append($val)
            });
        },


        _get_rgba_format: function (val) {
            var rgba = val.split(',')[0].match(/[A-Za-z0-9]{2}/g);
            rgba = rgba.map(function (v) {
                return parseInt(v, 16)
            }).join(",");
            return "rgba(" + rgba + "," + val.split(',')[1] + ")";
        }


    });
    registry.add('eagle_dashboard_item_preview', KsItemPreview);

    return {
        KsItemPreview: KsItemPreview
    };

});