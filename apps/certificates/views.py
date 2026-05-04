from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from .models import Certificate


@login_required
def my_certificates(request):
    certs = Certificate.objects.filter(student=request.user, is_valid=True).select_related('course')
    return render(request, 'certificates/my_certificates.html', {'certificates': certs})


@login_required
def certificate_view(request, pk):
    cert = get_object_or_404(Certificate, pk=pk, student=request.user, is_valid=True)
    return render(request, 'certificates/certificate_view.html', {'cert': cert})


@login_required
def certificate_download(request, pk):
    cert = get_object_or_404(Certificate, pk=pk, student=request.user, is_valid=True)
    if not cert.pdf_file:
        raise Http404('PDF not yet generated.')
    return FileResponse(cert.pdf_file.open('rb'), as_attachment=True, filename=f'certificate-{cert.course_title}.pdf')


def certificate_verify(request, code):
    """Public verification page — no login required."""
    cert = Certificate.objects.filter(verification_code=code).select_related('student', 'course').first()
    return render(request, 'certificates/verify.html', {'cert': cert, 'code': code})
