$(document).ready(function() {

  	$('[data-toggle="tooltip"]').tooltip()


    $(".datepicker").each(function(){
            $(this).datepicker({
            modal: true,
            uiLibrary: 'bootstrap4',
            iconsLibrary: 'fontawesome',
            format: 'yyyy-mm-dd',
            weekStartDay: 1,
        });

    });

    $("#button-save").click(function(){
        $("#form-edit").submit();
    });

});
