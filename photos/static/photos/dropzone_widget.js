Dropzone.autoDiscover = false;

document.addEventListener("DOMContentLoaded", function (event) {
    document.querySelectorAll('[id^="photos-dropzone-widget"]').forEach(element => {
        options = JSON.parse(element.textContent);
        options['params'] = {
            'csrfmiddlewaretoken': document.querySelector('input[name=\"csrfmiddlewaretoken\"]').getAttributeNode('value').value,
            'upload_id': document.querySelector('input[name=\"upload_id\"]').getAttributeNode('value').value,
        };
        options['paramName'] = 'file';
        new Dropzone('div.' + options.class, options);
    })
});
