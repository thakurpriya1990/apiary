import os
from io import BytesIO

from django.conf import settings
from docxtpl import DocxTemplate, InlineImage, R
from docx.shared import Mm
from disturbance.components.main.models import ApiaryGlobalSettings


def create_apiary_licence_pdf_contents(approval, proposal, copied_to_permit, approver, site_transfer_preview=None):

    licence_template = ApiaryGlobalSettings.objects.get(key=ApiaryGlobalSettings.KEY_APIARY_LICENCE_TEMPLATE_FILE)

    if licence_template._file:
        path_to_template = licence_template._file.path
    else:
        # Use default template file
        path_to_template = os.path.join(settings.BASE_DIR, 'disturbance', 'static', 'disturbance', 'apiary_authority_permit_template_v3.docx')

    doc = DocxTemplate(path_to_template)
    from disturbance.components.approvals.serializers import ApprovalSerializerForLicenceDoc

    path_to_image = os.path.join(settings.BASE_DIR, 'disturbance', 'static', 'disturbance', 'img', 'dbca-logo.jpg')
    serializer_context = {
            'approver': approver,
            'site_transfer_preview': site_transfer_preview,
            }
    context_obj = ApprovalSerializerForLicenceDoc(approval, context=serializer_context)
    context = context_obj.data
    context.update({
        'dbca_logo': InlineImage(doc, image_descriptor=path_to_image, width=Mm(135), height=Mm(20)),
        'page_break': R('\f'),
    })

    doc.render(context)

    temp_directory = settings.BASE_DIR + "/tmp/"
    try:
        os.stat(temp_directory)
    except:
        os.mkdir(temp_directory)

    f_name = temp_directory + 'apiary_licence_' + str(approval.id)
    new_doc_file = f_name + '.docx'
    new_pdf_file = f_name + '.pdf'
    doc.save(new_doc_file)
    os.system("libreoffice --headless --convert-to pdf " + new_doc_file + " --outdir " + temp_directory)

    file_contents = None
    with open(new_pdf_file, 'rb') as f:
        file_contents = f.read()
    os.remove(new_doc_file)
    os.remove(new_pdf_file)
    return file_contents
