from django.contrib import messages

def flash_form_errors(form, request):
    for field, error_list in form.errors.items():
        for error in error_list:
            if isinstance(error, list):
                for e in error:
                    messages.error(request, e)
            else:
                messages.error(request, error)