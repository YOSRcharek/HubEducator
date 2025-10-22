(function($) {
  'use strict';
  $(function() {
    $('.file-upload-browse').on('click', function() {
      var file = $(this).parent().parent().parent().find('.file-upload-default');
      file.trigger('click');
    });
    $('.file-upload-default').on('change', function() {
      $(this).parent().find('.form-control').val($(this).val().replace(/C:\\fakepath\\/i, ''));
    });
  });
})(jQuery);

  const pictureInput = document.getElementById('pictureInput');
  const fileName = document.getElementById('fileName');

  pictureInput.addEventListener('change', function() {
    if(this.files.length > 0){
      fileName.textContent = this.files[0].name;
    } else {
      fileName.textContent = '';
    }
  });