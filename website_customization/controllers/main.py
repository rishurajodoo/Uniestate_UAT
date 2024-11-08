# -*- coding: utf-8 -*-

from odoo.http import request
from odoo import http

class WebsiteActionController(http.Controller):

    @http.route(['/for_rent'], type='http', auth="public", website=True)
    def for_rent_backend(self, **kwargs):
        """
            Controller method to render the list of products available for rent.

            This method fetches all the products with the `for_rent` field set to `True`
            and renders the `products_template` with a title of 'For Rent Products'.

            :param kwargs: Additional parameters passed from the request (if any)
            :return: Rendered page displaying products available for rent
        """
        products = request.env['product.product'].sudo().search([('for_rent', '=', True)])

        return request.render('website_customization.products_template', {
            'products': products,
            'title': 'For Rent Products'
        })

    @http.route(['/for_sale'], type='http', auth="public", website=True)
    def for_sale_backend(self, **kwargs):
        """
            Controller method to render the list of products available for sale.

            This method fetches all the products with the `for_sale` field set to `True`
            and renders the `products_template` with a title of 'For Sale Products'.

            :param kwargs: Additional parameters passed from the request (if any)
            :return: Rendered page displaying products available for sale
        """
        products = request.env['product.product'].sudo().search([('for_sale', '=', True)])

        return request.render('website_customization.products_template', {
            'products': products,
            'title': 'For Sale Products'
        })

    @http.route('/website/enquire_now', type='http', auth='public', website=True)
    def render_enquire_modal(self, **kwargs):
        """
            Renders the 'Enquire Now' form modal on the website.

            This method serves the modal form template where users can input their details
            (name, phone, email) for further enquiries.
        """
        return request.render('website_customization.enquire_form_template')

    @http.route('/webform/enquiry/submit', type='http', auth='public', methods=['POST'],website=True)
    def create_crm_lead(self, **kwargs):
        """
            Creates a CRM lead based on the submitted enquiry form data.

            This method processes the form data (name, phone, email) submitted via POST,
            creates a new CRM lead in Odoo if any of the required fields are filled,
            and then redirects to the shop page.
        """

        name = kwargs.get('name', '')
        phone = kwargs.get('phone', '')
        email = kwargs.get('email', '')

        if name or phone or email:
            crm_lead_id = request.env['crm.lead'].sudo().create({
                "name": name,
                "email_from": email,
                "phone": phone
            })
            if crm_lead_id:
                return request.redirect('/shop')

