from menus.base import NavigationNode
from menus.menu_pool import menu_pool
from cms.menu_bases import CMSAttachMenu
#from cms.models import Page
from cms.utils.plugins import get_plugins
from django.utils.translation import ugettext_lazy as _

class AnchorMenu(CMSAttachMenu):
    """

    """
    name = 'anchor menu'

    def get_nodes(self, request):
        nodes = []

        page_obj = self.get_instances()[0]
        parent_url = page_obj.get_absolute_url()

        placeholder_name = "content"
        placeholder = page_obj.placeholders.get(slot=placeholder_name)
        plugins = get_plugins(request, placeholder, page_obj.get_template())

        anchors = []
        for plugin in plugins:
            try:
                #link = plugin.body.split('class="anchor-fixed"')[1].split('"')[1]
                link = plugin.body.split('name="')[1].split('"')[0]
                name = str(plugin).split()[0].title()
                anchors.append({'link':link, 'name':name})
            except:
                pass

        if anchors != []:
            newnode = NavigationNode(_(u"About"), parent_url + "#", 0)
            nodes.append(newnode)
            for id, anchor in enumerate(anchors):
                newnode = NavigationNode(anchor['name'], parent_url+"#" + anchor['link'], id+1)
                nodes.append(newnode)

        return nodes

menu_pool.register_menu(AnchorMenu)
