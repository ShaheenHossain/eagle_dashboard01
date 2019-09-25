# -*- coding: utf-8 -*-

from eagle import models, fields, api, _
from eagle.exceptions import ValidationError
import datetime
import json
from ..lib.eagle_date_filter_selections import eagle_get_date


class KsDashboardNinjaBoard(models.Model):
    _name = 'eagle_dashboard.board'
    _description = 'Dashboard Ninja'

    name = fields.Char(string="Dashboard Name", required=True, size=35)
    eagle_dashboard_items_ids = fields.One2many('eagle_dashboard.item', 'eagle_dashboard_board_id',
                                             string='Dashboard Items')
    eagle_dashboard_menu_name = fields.Char(string="Menu Name")
    eagle_dashboard_top_menu_id = fields.Many2one('ir.ui.menu', domain="[('parent_id','=',False)]",
                                               string="Show Under Menu")
    eagle_dashboard_client_action_id = fields.Many2one('ir.actions.client')
    eagle_dashboard_menu_id = fields.Many2one('ir.ui.menu')
    eagle_dashboard_state = fields.Char()
    eagle_dashboard_active = fields.Boolean(string="Active", default=True)
    eagle_dashboard_group_access = fields.Many2many('res.groups', string="Group Access")

    # DateFilter Fields
    eagle_dashboard_start_date = fields.Datetime(string="Start Date")
    eagle_dashboard_end_date = fields.Datetime(string="End Date")
    eagle_date_filter_selection = fields.Selection([
        ('l_none', 'All Time'),
        ('l_day', 'Today'),
        ('t_week', 'This Week'),
        ('t_month', 'This Month'),
        ('t_quarter', 'This Quarter'),
        ('t_year', 'This Year'),
        ('n_day', 'Next Day'),
        ('n_week', 'Next Week'),
        ('n_month', 'Next Month'),
        ('n_quarter', 'Next Quarter'),
        ('n_year', 'Next Year'),
        ('ls_day', 'Last Day'),
        ('ls_week', 'Last Week'),
        ('ls_month', 'Last Month'),
        ('ls_quarter', 'Last Quarter'),
        ('ls_year', 'Last Year'),
        ('l_week', 'Last 7 days'),
        ('l_month', 'Last 30 days'),
        ('l_quarter', 'Last 90 days'),
        ('l_year', 'Last 365 days'),
        ('l_custom', 'Custom Filter'),
    ], default='l_none', string="Default Date Filter")

    eagle_gridstack_config = fields.Char('Item Configurations')
    eagle_dashboard_default_template = fields.Many2one('eagle_dashboard.board_template',
                                                    default=lambda self: self.env.ref('eagle_dashboard.eagle_blank',
                                                                                      False),
                                                    string="Dashboard Template")

    eagle_set_interval = fields.Selection([
        (15000, '15 Seconds'),
        (30000, '30 Seconds'),
        (45000, '45 Seconds'),
        (60000, '1 minute'),
        (120000, '2 minute'),
        (300000, '5 minute'),
        (600000, '10 minute'),
    ], string="Default Update Interval", help="Update Interval for new items only")
    eagle_dashboard_menu_sequence = fields.Integer(string="Menu Sequence", default=10,
                                                help="Smallest sequence give high priority and Highest sequence give low priority")

    @api.model
    def create(self, vals):
        record = super(KsDashboardNinjaBoard, self).create(vals)
        if 'eagle_dashboard_top_menu_id' in vals and 'eagle_dashboard_menu_name' in vals:
            action_id = {
                'name': vals['eagle_dashboard_menu_name'] + " Action",
                'res_model': 'eagle_dashboard.board',
                'tag': 'eagle_dashboard',
                'params': {'eagle_dashboard_id': record.id},
            }
            record.eagle_dashboard_client_action_id = self.env['ir.actions.client'].sudo().create(action_id)

            record.eagle_dashboard_menu_id = self.env['ir.ui.menu'].sudo().create({
                'name': vals['eagle_dashboard_menu_name'],
                'active': vals.get('eagle_dashboard_active', True),
                'parent_id': vals['eagle_dashboard_top_menu_id'],
                'action': "ir.actions.client," + str(record.eagle_dashboard_client_action_id.id),
                'groups_id': vals.get('eagle_dashboard_group_access', False),
                'sequence': vals.get('eagle_dashboard_menu_sequence', 10)
            })

        if record.eagle_dashboard_default_template and record.eagle_dashboard_default_template.eagle_item_count:
            eagle_gridstack_config = {}
            template_data = json.loads(record.eagle_dashboard_default_template.eagle_gridstack_config)
            for item_data in template_data:
                dashboard_item = self.env.ref(item_data['item_id']).copy({'eagle_dashboard_board_id': record.id})
                eagle_gridstack_config[dashboard_item.id] = item_data['data']
            record.eagle_gridstack_config = json.dumps(eagle_gridstack_config)
        return record

    @api.multi
    def write(self, vals):
        record = super(KsDashboardNinjaBoard, self).write(vals)
        for rec in self:
            if 'eagle_dashboard_menu_name' in vals:
                if self.env.ref('eagle_dashboard.eagle_my_default_dashboard_board') and self.env.ref(
                        'eagle_dashboard.eagle_my_default_dashboard_board').sudo().id == rec.id:
                    if self.env.ref('eagle_dashboard.board_menu_root', False):
                        self.env.ref('eagle_dashboard.board_menu_root').sudo().name = vals['eagle_dashboard_menu_name']
                else:
                    rec.eagle_dashboard_menu_id.sudo().name = vals['eagle_dashboard_menu_name']
            if 'eagle_dashboard_group_access' in vals:
                if self.env.ref('eagle_dashboard.eagle_my_default_dashboard_board').id == rec.id:
                    if self.env.ref('eagle_dashboard.board_menu_root', False):
                        self.env.ref('eagle_dashboard.board_menu_root').groups_id = vals['eagle_dashboard_group_access']
                else:
                    rec.eagle_dashboard_menu_id.sudo().groups_id = vals['eagle_dashboard_group_access']
            if 'eagle_dashboard_active' in vals and rec.eagle_dashboard_menu_id:
                rec.eagle_dashboard_menu_id.sudo().active = vals['eagle_dashboard_active']

            if 'eagle_dashboard_top_menu_id' in vals:
                rec.eagle_dashboard_menu_id.write(
                    {'parent_id': vals['eagle_dashboard_top_menu_id']}
                )

            if 'eagle_dashboard_menu_sequence' in vals:
                rec.eagle_dashboard_menu_id.sudo().sequence = vals['eagle_dashboard_menu_sequence']

        return record

    @api.multi
    def unlink(self):
        if self.env.ref('eagle_dashboard.eagle_my_default_dashboard_board').id in self.ids:
            raise ValidationError(_("Default Dashboard can't be deleted."))
        else:
            for rec in self:
                rec.eagle_dashboard_client_action_id.sudo().unlink()
                rec.eagle_dashboard_menu_id.sudo().unlink()
                rec.eagle_dashboard_items_ids.unlink()
        res = super(KsDashboardNinjaBoard, self).unlink()
        return res

    @api.model
    def eagle_fetch_dashboard_data(self, eagle_dashboard_id, eagle_item_domain=False):
        """
        Return Dictionary of Dashboard Data.
        :param eagle_dashboard_id: Integer
        :param eagle_item_domain: List[List]
        :return: dict
        """

        self = self.eagle_set_date(eagle_dashboard_id)
        has_group_eagle_dashboard_manager = self.env.user.has_group('eagle_dashboard.eagle_dashboard_group_manager')
        dashboard_data = {
            'name': self.browse(eagle_dashboard_id).name,
            'eagle_dashboard_manager': has_group_eagle_dashboard_manager,
            'eagle_dashboard_list': self.search_read([], ['id', 'name']),
            'eagle_dashboard_start_date': self._context.get('ksDateFilterStartDate', False),
            'eagle_dashboard_end_date': self._context.get('ksDateFilterEndDate', False),
            'eagle_date_filter_selection': self._context.get('ksDateFilterSelection',
                                                          self.browse(eagle_dashboard_id).eagle_date_filter_selection),
            'eagle_gridstack_config': self.browse(eagle_dashboard_id).eagle_gridstack_config,
            'eagle_set_interval': self.browse(eagle_dashboard_id).eagle_set_interval,
        }

        if len(self.browse(eagle_dashboard_id).eagle_dashboard_items_ids) < 1:
            dashboard_data['eagle_item_data'] = False
        else:
            if eagle_item_domain:
                try:
                    items = self.eagle_fetch_item(self.eagle_dashboard_items_ids.search(
                        [['eagle_dashboard_board_id', '=', eagle_dashboard_id]] + eagle_item_domain).ids, eagle_dashboard_id)
                except Exception as e:
                    items = self.eagle_fetch_item(self.browse(eagle_dashboard_id).eagle_dashboard_items_ids.ids, eagle_dashboard_id)
                    dashboard_data['eagle_item_data'] = items
                    return dashboard_data
            else:
                items = self.eagle_fetch_item(self.browse(eagle_dashboard_id).eagle_dashboard_items_ids.ids, eagle_dashboard_id)

            dashboard_data['eagle_item_data'] = items
        return dashboard_data

    @api.model
    def eagle_fetch_item(self, item_list, eagle_dashboard_id):
        """
        :rtype: object
        :param item_list: list of item ids.
        :return: {'id':[item_data]}
        """
        self = self.eagle_set_date(eagle_dashboard_id)
        items = {}
        item_model = self.env['eagle_dashboard.item']
        for item_id in item_list:
            item = self.eagle_fetch_item_data(item_model.browse(item_id))
            items[item['id']] = item
        return items

    # fetching Item info (Divided to make function inherit easily)
    def eagle_fetch_item_data(self, rec):
        """
        :rtype: object
        :param item_id: item object
        :return: object with formatted item data
        """
        if rec.eagle_actions:
            action = {}
            action['name'] = rec.eagle_actions.name
            action['type'] = rec.eagle_actions.type
            action['res_model'] = rec.eagle_actions.res_model
            action['views'] = rec.eagle_actions.views
            action['view_mode'] = rec.eagle_actions.view_mode
            action['target'] = 'current'
        else:
            action = False
        item = {
            'name': rec.name if rec.name else rec.eagle_model_id.name if rec.eagle_model_id else "Name",
            'eagle_background_color': rec.eagle_background_color,
            'eagle_font_color': rec.eagle_font_color,
            # 'eagle_domain': rec.eagle_domain.replace('"%UID"', str(
            #     self.env.user.id)) if rec.eagle_domain and "%UID" in rec.eagle_domain else rec.eagle_domain,
            'eagle_domain': rec.eagle_convert_into_proper_domain(rec.eagle_domain, rec),
            'eagle_dashboard_id': rec.eagle_dashboard_board_id.id,
            'eagle_icon': rec.eagle_icon,
            'eagle_model_id': rec.eagle_model_id.id,
            'eagle_model_name': rec.eagle_model_name,
            'eagle_model_display_name': rec.eagle_model_id.name,
            'eagle_record_count_type': rec.eagle_record_count_type,
            'eagle_record_count': rec.eagle_record_count,
            'id': rec.id,
            'eagle_layout': rec.eagle_layout,
            'eagle_icon_select': rec.eagle_icon_select,
            'eagle_default_icon': rec.eagle_default_icon,
            'eagle_default_icon_color': rec.eagle_default_icon_color,
            # Pro Fields
            'eagle_dashboard_item_type': rec.eagle_dashboard_item_type,
            'eagle_chart_item_color': rec.eagle_chart_item_color,
            'eagle_chart_groupby_type': rec.eagle_chart_groupby_type,
            'eagle_chart_relation_groupby': rec.eagle_chart_relation_groupby.id,
            'eagle_chart_relation_groupby_name': rec.eagle_chart_relation_groupby.name,
            'eagle_chart_date_groupby': rec.eagle_chart_date_groupby,
            'eagle_record_field': rec.eagle_record_field.id if rec.eagle_record_field else False,
            'eagle_chart_data': rec.eagle_chart_data,
            'eagle_list_view_data': rec.eagle_list_view_data,
            'eagle_chart_data_count_type': rec.eagle_chart_data_count_type,
            'eagle_bar_chart_stacked': rec.eagle_bar_chart_stacked,
            'eagle_semi_circle_chart': rec.eagle_semi_circle_chart,
            'eagle_list_view_type': rec.eagle_list_view_type,
            'eagle_list_view_group_fields': rec.eagle_list_view_group_fields.ids if rec.eagle_list_view_group_fields else False,
            'eagle_previous_period': rec.eagle_previous_period,
            'eagle_kpi_data': rec.eagle_kpi_data,
            'eagle_goal_enable': rec.eagle_goal_enable,
            'eagle_model_id_2': rec.eagle_model_id_2.id,
            'eagle_record_field_2': rec.eagle_record_field_2.id,
            'eagle_data_comparison': rec.eagle_data_comparison,
            'eagle_target_view': rec.eagle_target_view,
            'eagle_date_filter_selection': rec.eagle_date_filter_selection,
            'eagle_show_data_value': rec.eagle_show_data_value,
            'eagle_update_items_data': rec.eagle_update_items_data,
            # 'action_id': rec.eagle_actions.id if rec.eagle_actions else False,
            'sequence': 0,
            'max_sequnce': len(rec.eagle_action_lines) if rec.eagle_action_lines else False,
            'action': action
        }
        return item

    def eagle_set_date(self, eagle_dashboard_id):
        if self._context.get('ksDateFilterSelection', False):
            eagle_date_filter_selection = self._context['ksDateFilterSelection']
            if eagle_date_filter_selection == 'l_custom':
                self = self.with_context(
                    ksDateFilterStartDate=fields.datetime.strptime(self._context['ksDateFilterStartDate'],
                                                                   "%Y-%m-%dT%H:%M:%S.%fz"))
                self = self.with_context(
                    ksDateFilterEndDate=fields.datetime.strptime(self._context['ksDateFilterEndDate'],
                                                                 "%Y-%m-%dT%H:%M:%S.%fz"))

        else:
            eagle_date_filter_selection = self.browse(eagle_dashboard_id).eagle_date_filter_selection
            self = self.with_context(ksDateFilterStartDate=self.browse(eagle_dashboard_id).eagle_dashboard_start_date)
            self = self.with_context(ksDateFilterEndDate=self.browse(eagle_dashboard_id).eagle_dashboard_end_date)
            self = self.with_context(ksDateFilterSelection=eagle_date_filter_selection)

        if eagle_date_filter_selection not in ['l_custom', 'l_none']:
            eagle_date_data = eagle_get_date(eagle_date_filter_selection)
            self = self.with_context(ksDateFilterStartDate=eagle_date_data["selected_start_date"])
            self = self.with_context(ksDateFilterEndDate=eagle_date_data["selected_end_date"])

        return self

    @api.multi
    def load_previous_data(self):

        for rec in self:
            if rec.eagle_dashboard_menu_id and rec.eagle_dashboard_menu_id.action._table == 'ir_act_window':
                action_id = {
                    'name': rec['eagle_dashboard_menu_name'] + " Action",
                    'res_model': 'eagle_dashboard.board',
                    'tag': 'eagle_dashboard',
                    'params': {'eagle_dashboard_id': rec.id},
                }
                rec.eagle_dashboard_client_action_id = self.env['ir.actions.client'].sudo().create(action_id)
                rec.eagle_dashboard_menu_id.write(
                    {'action': "ir.actions.client," + str(rec.eagle_dashboard_client_action_id.id)})

    def eagle_view_items_view(self):
        self.ensure_one()
        return {
            'name': _("Dashboard Items"),
            'res_model': 'eagle_dashboard.item',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [(False, 'tree'), (False, 'form')],
            'type': 'ir.actions.act_window',
            'domain': [('eagle_dashboard_board_id', '!=', False)],
            'search_view_id': self.env.ref('eagle_dashboard.eagle_item_search_view').id,
            'context': {
                'search_default_eagle_dashboard_board_id': self.id,
                'group_by': 'eagle_dashboard_board_id',
            },
            'help': _('''<p class="o_view_nocontent_smiling_face">
                                        You can find all items related to Dashboard Here.</p>
                                    '''),

        }

    # fetching Item info (Divided to make function inherit easily)
    def eagle_export_item_data(self, rec):
        eagle_chart_measure_field = []
        eagle_chart_measure_field_2 = []
        for res in rec.eagle_chart_measure_field:
            eagle_chart_measure_field.append(res.name)
        for res in rec.eagle_chart_measure_field_2:
            eagle_chart_measure_field_2.append(res.name)

        eagle_list_view_group_fields = []
        for res in rec.eagle_list_view_group_fields:
            eagle_list_view_group_fields.append(res.name)

        eagle_goal_lines = []
        for res in rec.eagle_goal_lines:
            goal_line = {
                'eagle_goal_date': datetime.datetime.strftime(res.eagle_goal_date, '%b %d, %Y'),
                'eagle_goal_value': res.eagle_goal_value,
            }
            eagle_goal_lines.append(goal_line)

        eagle_action_lines = []
        for res in rec.eagle_action_lines:
            action_line = {
                'eagle_item_action_field': res.eagle_item_action_field.name,
                'eagle_item_action_date_groupby': res.eagle_item_action_date_groupby,
                'eagle_chart_type': res.eagle_chart_type,
                'sequence': res.sequence,
            }
            eagle_action_lines.append(action_line)

        eagle_list_view_field = []
        for res in rec.eagle_list_view_fields:
            eagle_list_view_field.append(res.name)
        item = {
            'name': rec.name if rec.name else rec.eagle_model_id.name if rec.eagle_model_id else "Name",
            'eagle_background_color': rec.eagle_background_color,
            'eagle_font_color': rec.eagle_font_color,
            'eagle_domain': rec.eagle_domain,
            'eagle_icon': rec.eagle_icon,
            'eagle_id': rec.id,
            'eagle_model_id': rec.eagle_model_name,
            'eagle_record_count': rec.eagle_record_count,
            'eagle_layout': rec.eagle_layout,
            'eagle_icon_select': rec.eagle_icon_select,
            'eagle_default_icon': rec.eagle_default_icon,
            'eagle_default_icon_color': rec.eagle_default_icon_color,
            'eagle_record_count_type': rec.eagle_record_count_type,
            # Pro Fields
            'eagle_dashboard_item_type': rec.eagle_dashboard_item_type,
            'eagle_chart_item_color': rec.eagle_chart_item_color,
            'eagle_chart_groupby_type': rec.eagle_chart_groupby_type,
            'eagle_chart_relation_groupby': rec.eagle_chart_relation_groupby.name,
            'eagle_chart_date_groupby': rec.eagle_chart_date_groupby,
            'eagle_record_field': rec.eagle_record_field.name,
            'eagle_chart_sub_groupby_type': rec.eagle_chart_sub_groupby_type,
            'eagle_chart_relation_sub_groupby': rec.eagle_chart_relation_sub_groupby.name,
            'eagle_chart_date_sub_groupby': rec.eagle_chart_date_sub_groupby,
            'eagle_chart_data_count_type': rec.eagle_chart_data_count_type,
            'eagle_chart_measure_field': eagle_chart_measure_field,
            'eagle_chart_measure_field_2': eagle_chart_measure_field_2,
            'eagle_list_view_fields': eagle_list_view_field,
            'eagle_list_view_group_fields': eagle_list_view_group_fields,
            'eagle_list_view_type': rec.eagle_list_view_type,
            'eagle_record_data_limit': rec.eagle_record_data_limit,
            'eagle_sort_by_order': rec.eagle_sort_by_order,
            'eagle_sort_by_field': rec.eagle_sort_by_field.name,
            'eagle_date_filter_field': rec.eagle_date_filter_field.name,
            'eagle_goal_enable': rec.eagle_goal_enable,
            'eagle_standard_goal_value': rec.eagle_standard_goal_value,
            'eagle_goal_liness': eagle_goal_lines,
            'eagle_date_filter_selection': rec.eagle_date_filter_selection,
            'eagle_item_start_date': datetime.datetime.strftime(rec.eagle_item_start_date,
                                                             '%b %d, %Y') if rec.eagle_item_start_date else False,
            'eagle_item_end_date': datetime.datetime.strftime(rec.eagle_item_end_date,
                                                           '%b %d, %Y') if rec.eagle_item_end_date else False,
            'eagle_date_filter_selection_2': rec.eagle_date_filter_selection_2,
            'eagle_item_start_date_2': datetime.datetime.strftime(rec.eagle_item_start_date_2,
                                                               '%b %d, %Y') if rec.eagle_item_start_date_2 else False,
            'eagle_item_end_date_2': datetime.datetime.strftime(rec.eagle_item_end_date_2,
                                                             '%b %d, %Y') if rec.eagle_item_end_date_2 else False,
            'eagle_previous_period': rec.eagle_previous_period,
            'eagle_target_view': rec.eagle_target_view,
            'eagle_data_comparison': rec.eagle_data_comparison,
            'eagle_record_count_type_2': rec.eagle_record_count_type_2,
            'eagle_record_field_2': rec.eagle_record_field_2.name,
            'eagle_model_id_2': rec.eagle_model_id_2.model,
            'eagle_date_filter_field_2': rec.eagle_date_filter_field_2.name,
            'eagle_action_liness': eagle_action_lines,
            'eagle_compare_period': rec.eagle_compare_period,
            'eagle_year_period': rec.eagle_year_period,
        }
        return item

    @api.model
    def eagle_dashboard_export(self, eagle_dashboard_ids):
        eagle_dashboard_data = []
        eagle_dashboard_export_data = {}
        eagle_dashboard_ids = json.loads(eagle_dashboard_ids)
        for eagle_dashboard_id in eagle_dashboard_ids:
            dashboard_data = {
                'name': self.browse(eagle_dashboard_id).name,
                'eagle_dashboard_menu_name': self.browse(eagle_dashboard_id).eagle_dashboard_menu_name,
                'eagle_gridstack_config': self.browse(eagle_dashboard_id).eagle_gridstack_config,
            }
            if len(self.browse(eagle_dashboard_id).eagle_dashboard_items_ids) < 1:
                dashboard_data['eagle_item_data'] = False
            else:
                items = []
                for rec in self.browse(eagle_dashboard_id).eagle_dashboard_items_ids:
                    item = self.eagle_export_item_data(rec)
                    items.append(item)

                dashboard_data['eagle_item_data'] = items

            eagle_dashboard_data.append(dashboard_data)

            eagle_dashboard_export_data = {
                'eagle_file_format': 'eagle_dashboard_export_file',
                'eagle_dashboard_data': eagle_dashboard_data
            }
        return eagle_dashboard_export_data

    @api.model
    def eagle_import_dashboard(self, file):
        try:
            # eagle_dashboard_data = json.loads(file)
            eagle_dashboard_file_read = json.loads(file)
        except:
            raise ValidationError(_("This file is not supported"))

        if 'eagle_file_format' in eagle_dashboard_file_read and eagle_dashboard_file_read[
            'eagle_file_format'] == 'eagle_dashboard_export_file':
            eagle_dashboard_data = eagle_dashboard_file_read['eagle_dashboard_data']
        else:
            raise ValidationError(_("Current Json File is not properly formatted according to Dashboard Ninja Model."))

        eagle_dashboard_key = ['name', 'eagle_dashboard_menu_name', 'eagle_gridstack_config']
        eagle_dashboard_item_key = ['eagle_model_id', 'eagle_chart_measure_field', 'eagle_list_view_fields', 'eagle_record_field',
                                 'eagle_chart_relation_groupby', 'eagle_id']

        # Fetching dashboard model info
        for data in eagle_dashboard_data:
            if not all(key in data for key in eagle_dashboard_key):
                raise ValidationError(
                    _("Current Json File is not properly formatted according to Dashboard Ninja Model."))
            vals = {
                'name': data['name'],
                'eagle_dashboard_menu_name': data['eagle_dashboard_menu_name'],
                'eagle_dashboard_top_menu_id': self.env.ref("eagle_dashboard.board_menu_root").id,
                'eagle_dashboard_active': True,
                'eagle_gridstack_config': data['eagle_gridstack_config'],
                'eagle_dashboard_default_template': self.env.ref("eagle_dashboard.eagle_blank").id,
                'eagle_dashboard_group_access': False,

            }
            # Creating Dashboard
            dashboard_id = self.create(vals)

            if data['eagle_gridstack_config']:
                eagle_gridstack_config = eval(data['eagle_gridstack_config'])
            eagle_grid_stack_config = {}

            if data['eagle_item_data']:
                # Fetching dashboard item info
                for item in data['eagle_item_data']:
                    if not all(key in item for key in eagle_dashboard_item_key):
                        raise ValidationError(
                            _("Current Json File is not properly formatted according to Dashboard Ninja Model."))

                    eagle_model = item['eagle_model_id'].replace(".", "_")

                    eagle_measure_field_ids = []
                    eagle_measure_field_2_ids = []

                    model = self.env['ir.model'].search([('model', '=', item['eagle_model_id'])])

                    if not model:
                        raise ValidationError(_(
                            "Please Install the Module which contains the following Model : %s " % item['eagle_model_id']))

                    if item['eagle_model_id_2']:
                        model_2 = self.env['ir.model'].search([('model', '=', item['eagle_model_id_2'])])
                        if not model_2:
                            raise ValidationError(_(
                                "Please Install the Module which contains the following Model : %s " % item[
                                    'eagle_model_id_2']))

                    for eagle_measure in item['eagle_chart_measure_field']:
                        for x in self.env['ir.model'].search([('model', '=', item['eagle_model_id'])]).modules.split(", "):
                            measure_id = x + '.field_' + eagle_model + "__" + eagle_measure
                            eagle_measure_id = self.env.ref(measure_id, False)
                            if eagle_measure_id:
                                eagle_measure_field_ids.append(eagle_measure_id.id)
                    item['eagle_chart_measure_field'] = [(6, 0, eagle_measure_field_ids)]

                    for eagle_measure in item['eagle_chart_measure_field_2']:
                        for x in self.env['ir.model'].search([('model', '=', item['eagle_model_id'])]).modules.split(", "):
                            measure_id = x + '.field_' + eagle_model + "__" + eagle_measure
                            eagle_measure_id = self.env.ref(measure_id, False)
                            if eagle_measure_id:
                                eagle_measure_field_2_ids.append(eagle_measure_id.id)
                    item['eagle_chart_measure_field_2'] = [(6, 0, eagle_measure_field_2_ids)]

                    eagle_list_view_group_fields = []
                    for eagle_measure in item['eagle_list_view_group_fields']:
                        for x in self.env['ir.model'].search([('model', '=', item['eagle_model_id'])]).modules.split(", "):
                            measure_id = x + '.field_' + eagle_model + "__" + eagle_measure
                            eagle_measure_id = self.env.ref(measure_id, False)
                            if eagle_measure_id:
                                eagle_list_view_group_fields.append(eagle_measure_id.id)
                    item['eagle_list_view_group_fields'] = [(6, 0, eagle_list_view_group_fields)]

                    eagle_list_view_field_ids = []
                    for eagle_list_field in item['eagle_list_view_fields']:
                        for x in self.env['ir.model'].search([('model', '=', item['eagle_model_id'])]).modules.split(", "):
                            list_field_id = x + '.field_' + eagle_model + "__" + eagle_list_field
                            eagle_list_field_id = self.env.ref(list_field_id, False)
                            if eagle_list_field_id:
                                eagle_list_view_field_ids.append(eagle_list_field_id.id)
                    item['eagle_list_view_fields'] = [(6, 0, eagle_list_view_field_ids)]

                    if item['eagle_record_field']:
                        eagle_record_field = item['eagle_record_field']
                        for x in self.env['ir.model'].search([('model', '=', item['eagle_model_id'])]).modules.split(", "):
                            record_id = x + '.field_' + eagle_model + "__" + eagle_record_field
                            eagle_record_id = self.env.ref(record_id, False)
                            if eagle_record_id:
                                item['eagle_record_field'] = eagle_record_id.id

                    if item['eagle_date_filter_field']:
                        eagle_date_filter_field = item['eagle_date_filter_field']
                        for x in self.env['ir.model'].search([('model', '=', item['eagle_model_id'])]).modules.split(", "):
                            record_id = x + '.field_' + eagle_model + "__" + eagle_date_filter_field
                            eagle_record_id = self.env.ref(record_id, False)
                            if eagle_record_id:
                                item['eagle_date_filter_field'] = eagle_record_id.id

                    if item['eagle_chart_relation_groupby']:
                        eagle_group_by = item['eagle_chart_relation_groupby']
                        for x in self.env['ir.model'].search([('model', '=', item['eagle_model_id'])]).modules.split(", "):
                            field_id = x + '.field_' + eagle_model + "__" + eagle_group_by
                            eagle_chart_relation_groupby = self.env.ref(field_id, False)
                            if eagle_chart_relation_groupby:
                                item['eagle_chart_relation_groupby'] = eagle_chart_relation_groupby.id

                    if item['eagle_chart_relation_sub_groupby']:
                        eagle_group_by = item['eagle_chart_relation_sub_groupby']
                        for x in self.env['ir.model'].search([('model', '=', item['eagle_model_id'])]).modules.split(", "):
                            field_id = x + '.field_' + eagle_model + "__" + eagle_group_by
                            eagle_chart_relation_sub_groupby = self.env.ref(field_id, False)
                            if eagle_chart_relation_sub_groupby:
                                item['eagle_chart_relation_sub_groupby'] = eagle_chart_relation_sub_groupby.id

                    # Sort by field : Many2one Entery
                    if item['eagle_sort_by_field']:
                        eagle_group_by = item['eagle_sort_by_field']
                        for x in self.env['ir.model'].search([('model', '=', item['eagle_model_id'])]).modules.split(", "):
                            field_id = x + '.field_' + eagle_model + "__" + eagle_group_by
                            eagle_sort_by_field = self.env.ref(field_id, False)
                            if eagle_sort_by_field:
                                item['eagle_sort_by_field'] = eagle_sort_by_field.id

                    eagle_model_id = self.env['ir.model'].search([('model', '=', item['eagle_model_id'])]).id
                    if (item['eagle_model_id_2']):
                        eagle_model_2 = item['eagle_model_id_2'].replace(".", "_")
                        eagle_model_id_2 = self.env['ir.model'].search([('model', '=', item['eagle_model_id_2'])]).id
                        if item['eagle_record_field_2']:
                            eagle_record_field = item['eagle_record_field_2']
                            for x in self.env['ir.model'].search([('model', '=', item['eagle_model_id_2'])]).modules.split(
                                    ", "):
                                record_id = x + '.field_' + eagle_model_2 + "__" + eagle_record_field
                                eagle_record_id = self.env.ref(record_id, False)
                                if eagle_record_id:
                                    item['eagle_record_field_2'] = eagle_record_id.id
                        if item['eagle_date_filter_field_2']:
                            eagle_date_filter_field = item['eagle_date_filter_field_2']
                            for x in self.env['ir.model'].search([('model', '=', item['eagle_model_id_2'])]).modules.split(
                                    ", "):
                                record_id = x + '.field_' + eagle_model_2 + "__" + eagle_date_filter_field
                                eagle_record_id = self.env.ref(record_id, False)
                                if eagle_record_id:
                                    item['eagle_date_filter_field_2'] = eagle_record_id.id
                        item['eagle_model_id_2'] = eagle_model_id_2
                    else:
                        item['eagle_date_filter_field_2'] = False
                        item['eagle_record_field_2'] = False
                    eagle_model_id = item['eagle_model_id']
                    item['eagle_model_id'] = self.env['ir.model'].search([('model', '=', item['eagle_model_id'])]).id
                    item['eagle_dashboard_board_id'] = dashboard_id.id

                    eagle_goal_lines = item['eagle_goal_liness'].copy() if item.get('eagle_goal_liness', False) else False
                    item['eagle_goal_liness'] = False

                    item['eagle_item_start_date'] = datetime.datetime.strptime(item['eagle_item_start_date'], '%b %d, %Y') if \
                        item[
                            'eagle_item_start_date'] else False
                    item['eagle_item_end_date'] = datetime.datetime.strptime(item['eagle_item_end_date'], '%b %d, %Y') if \
                        item[
                            'eagle_item_end_date'] else False
                    item['eagle_item_start_date_2'] = datetime.datetime.strptime(item['eagle_item_start_date_2'],
                                                                              '%b %d, %Y') if \
                        item[
                            'eagle_item_start_date_2'] else False
                    item['eagle_item_end_date_2'] = datetime.datetime.strptime(item['eagle_item_end_date_2'], '%b %d, %Y') if \
                        item[
                            'eagle_item_end_date_2'] else False

                    eagle_action_lines = item['eagle_action_liness'].copy() if item.get('eagle_action_liness', False) else False
                    # Creating dashboard items
                    eagle_item = self.env['eagle_dashboard.item'].create(item)
                    if eagle_goal_lines and len(eagle_goal_lines) != 0:
                        for line in eagle_goal_lines:
                            line['eagle_goal_date'] = datetime.datetime.strptime(line['eagle_goal_date'], '%b %d, %Y')
                            line['eagle_dashboard_item'] = eagle_item.id
                            self.env['eagle_dashboard.item_goal'].create(line)

                    if eagle_action_lines and len(eagle_action_lines) != 0:

                        for line in eagle_action_lines:
                            if line['eagle_item_action_field']:
                                eagle_item_action_field = line['eagle_item_action_field']
                                for x in self.env['ir.model'].search([('model', '=', eagle_model_id)]).modules.split(
                                        ", "):
                                    record_id = x + '.field_' + eagle_model + "__" + eagle_item_action_field
                                    eagle_record_id = self.env.ref(record_id, False)
                                    if eagle_record_id:
                                        line['eagle_item_action_field'] = eagle_record_id.id
                            line['eagle_dashboard_item_id'] = eagle_item.id
                            self.env['eagle_dashboard.item_action'].create(line)

                    if data['eagle_gridstack_config'] and str(item['eagle_id']) in eagle_gridstack_config:
                        eagle_grid_stack_config[str(eagle_item.id)] = eagle_gridstack_config[str(item['eagle_id'])]

                self.browse(dashboard_id.id).write({
                    'eagle_gridstack_config': json.dumps(eagle_grid_stack_config)
                })

        return "Success"


class KsDashboardNinjaTemplate(models.Model):
    _name = 'eagle_dashboard.board_template'
    _description = 'Dashboard Ninja Template'
    name = fields.Char()
    eagle_gridstack_config = fields.Char()
    eagle_item_count = fields.Integer()
