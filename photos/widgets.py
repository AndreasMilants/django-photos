from django import forms


class DropzoneWidget(forms.widgets.FileInput):
    template_name = 'photos/forms/widgets/dropzone.html'

    class Media:
        js = ("photos/dropzone/dropzone.min.js", 'photos/dropzone_widget.js')
        css = {
            'all': ("photos/dropzone/basic.min.css", "photos/dropzone/dropzone.min.css",
                    "photos/dropzone/simple-styling.css")
        }

    def __init__(self, attrs=None, options=None):
        super().__init__(attrs)
        if options is None:
            options = {}
        self.options = options

    def get_context(self, name, value, attrs):
        current_class = attrs.get('class')
        custom_class = 'photos-dropzone-widget-' + name
        if current_class:
            attrs['class'] = current_class + ' ' + custom_class
        else:
            attrs['class'] = custom_class
        context = super().get_context(name, value, attrs)
        self.options.update({
            'class': custom_class,
            'paramName': name
        })
        context['options'] = self.options
        return context
