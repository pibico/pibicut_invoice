# -*- coding: utf-8 -*-
# Copyright (c) 2021, PibiCo and contributors
# For license information, please see license.txt
import frappe
from frappe import _, msgprint, throw
from datetime import datetime, timedelta

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import SquareModuleDrawer, GappedSquareModuleDrawer, CircleModuleDrawer, RoundedModuleDrawer, VerticalBarsDrawer, HorizontalBarsDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask, SquareGradiantColorMask, HorizontalGradiantColorMask, VerticalGradiantColorMask, ImageColorMask

from PIL import Image
import base64, os
from io import BytesIO

def get_qrCode(input_data, logo):
  qr = qrcode.QRCode(
        version=6,
        box_size=4,
        border=3
  )
  qr.add_data(input_data)
  qr.make(fit=True)
  path = frappe.utils.get_bench_path()
  site_name = frappe.utils.get_url().replace("http://","").replace("https://","")
  if ":" in site_name:
    pos = site_name.find(":")
    site_name = site_name[:pos]
  
  if logo:
    embedded = os.path.join(path, "sites", site_name, 'public', logo[1:])
    img = qr.make_image(image_factory=StyledPilImage, module_drawer=GappedSquareModuleDrawer(), eye_drawer=SquareModuleDrawer(), embeded_image_path=embedded)
  else:
    img = qr.make_image(image_factory=StyledPilImage, module_drawer=GappedSquareModuleDrawer(), eye_drawer=SquareModuleDrawer())
  #qr = qrcode.make(input_str)
  temp = BytesIO()
  img.save(temp, "PNG")
  temp.seek(0)
  b64 = base64.b64encode(temp.read())
  return "data:image/png;base64,{0}".format(b64.decode("utf-8"))

def getTLVForValue(tagNum, tagValue):
  tag = "{:02x}".format(int(tagNum))
  tagLen = "{:02x}".format(len(tagValue.encode('utf-8')))
  tagValue = tagValue.encode('utf-8').hex()
  tagList = [tag, tagLen, tagValue]
  
  return "".join(tagList)

def generate_tlv_qr(doc, method):
  ## Form xml for QRCode
  xml = """<QRCode>
				<SellerName>{customer}</SellerName>
				<DateAndTime>{posting_date}</DateAndTime>
				<InvoiceTotal>{invoice_total}</InvoiceTotal>
				<VATTotal>{vat_total}</VATTotal>
			</QRCode>""".format(customer=doc.company, posting_date=doc.posting_date, invoice_total=doc.grand_total, vat_total=doc.total_taxes_and_charges)
  ## Get Seller's name from Company Tag 01
  if doc.company_name_in_arabic:
    seller_name = doc.company_name_in_arabic
  else:
    seller_name = doc.company
  tlv_t1 = getTLVForValue("1", seller_name)
  ## Get VAT Number from Company Tax ID Tag 02
  vat_number = doc.company_tax_id
  tlv_t2 = getTLVForValue("2", vat_number)
  ## Combine Posting Date and Time to produce Posting Datetime Tag 03
  ts_date = datetime.strptime(doc.posting_date, '%Y-%m-%d')
  ts_time = datetime.strptime(doc.posting_time, '%H:%M:%S.%f').time()
  ts_datetime = datetime.combine(ts_date, ts_time).strftime('%Y-%m-%dT%H:%M:%SZ')
  tlv_t3 = getTLVForValue("3", ts_datetime)
  ## Get Invoice Total with VAT Tag 04
  invoice_total = doc.grand_total 
  tlv_t4 = getTLVForValue("4", str("%.2f" % invoice_total))
  ## Get VAT Tag 05
  vat = doc.total_taxes_and_charges
  tlv_t5 = getTLVForValue("5", str("%.2f" % vat))
  ## Get HashedXML (future)
  #hashedXML = doc.hashedxml
  #tlv_t6 = getTLVForValue("6", hashedXML)
  ## Get Key (future)
  #key = doc.key
  #tlv_t7 = getTLVForValue("7", key)
  ## Get Signature (future)
  #signature = doc.signature
  #tlv_t8 = getTLVForValue("8", signature)
  
  ## Create hex string
  #tlv = [tlv_t1, tlv_t2, tlv_t3, tlv_t4, tlv_t5, tlv_t6, tlv_t7, tlv_t8] # (future)
  tlv = [tlv_t1, tlv_t2, tlv_t3, tlv_t4, tlv_t5]
  tlv_data = "".join(tlv)
  ## Encode hex bytearray from hex string
  base64_data = base64.b64encode(bytearray.fromhex(tlv_data))
  ## Function for generating TLV QR Code on Sales Invoice
  doc.base64_data = base64_data
  ## Generate and fill TLV QR Code image based on encoded string
  if base64_data:
    doc.qr_code = get_qrCode(base64_data, doc.logo)
  else:
    doc.qr_code = None