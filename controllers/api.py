from odoo import http
import json


class MyApi(http.Controller):

    @http.route('/my_api/hello', type='json', auth='none', methods=['GET'])
    def hello_world(self, **kw):
        data = {'message': 'Hello, World!'}
        return json.dumps(data)