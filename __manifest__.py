# -*- coding: utf-8 -*-
{
    'name': "Eagle Dashboard",

    'summary': """
    Eagle Dashboard ! It is dashboard eagle apps in the market.
    """,

    'description': """
        Eagle Dashboard v12.0,
        Eagle Dashboard, 
        Dashboard,
        Eagle apps,
        Dashboard app,
        HR Dashboard,
        Sales Dashboard, 
        inventory Dashboard, 
        Lead Dashboard, 
        Opportunity Dashboard, 
        CRM Dashboard,
	    POS,
	    POS Dashboard,
	    Connectors,
	    Web Dynamic,
	    Report Import/Export,
	    Date Filter,
	    HR,
	    Sales,
	    Theme,
	    Tile Dashboard,
	    Dashboard Widgets,
	    Dashboard Manager,
	    Debranding,
	    Customize Dashboard,
	    Graph Dashboard,
	    Charts Dashboard,
	    Invoice Dashboard,
	    Project management,
    """,

    'author': "Eagle ERP",
    'license': 'OPL-1',
    'currency': 'EUR',
    'price': 29.0,
    'website': "https://www.eagle-erp.com",
    'maintainer': 'Eagle ERP.',
    'live_test_url': 'https://eagle-erp.com',
    'category': 'Tools',
    'version': '12.0.1',
    'support': 'sales@eagle-erp.com',
    'images': ['static/description/banner.gif'],

    'depends': ['base', 'web', 'base_setup'],

    'data': [
        'security/ir.model.access.csv',
        'security/eagle_security_groups.xml',
        'data/eagle_default_data.xml',
        'views/eagle_dashboard_view.xml',
        'views/eagle_dashboard_item_view.xml',
        'views/eagle_dashboard_assets.xml',
        'views/eagle_dashboard_action.xml',
    ],

    'qweb': [
        'static/src/xml/eagle_dashboard_templates.xml',
        'static/src/xml/eagle_dashboard_item_templates.xml',
        'static/src/xml/eagle_dashboard_item_theme.xml',
        'static/src/xml/eagle_widget_toggle.xml',
        'static/src/xml/eagle_dashboard_pro.xml',
        'static/src/xml/eagle_import_list_view_template.xml',
        'static/src/xml/eagle_quick_edit_view.xml',
    ],

    'demo': [
        'demo/eagle_dashboard_demo.xml',
    ],

    'uninstall_hook': 'uninstall_hook',

}
