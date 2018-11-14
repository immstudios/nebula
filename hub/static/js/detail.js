$(document).ready(function() {

  	$('[data-toggle="tooltip"]').tooltip()

    $('.datepicker').datepicker({
            uiLibrary: 'bootstrap4',
            iconsLibrary: 'fontawesome',
            format: 'yyyy-mm-dd',
            weekStartDay: 1,
        });

    $("#button-save").click(function(){
        $("#form-edit").submit();
    });

});
