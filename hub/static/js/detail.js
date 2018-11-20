function save_asset() {
    console.log($("#input-duration").val());
    console.log($("#input-form-duration").val());
    if ($("#input-duration").val() != $("#input-form-duration").val()){
        $("#input-form-duration").val($("#input-duration").val());
        console.log("changing duration to", $("#input-form-duration").val());
    }
    $("#form-edit").submit();
}


$(document).ready(function(){

    if (window.history.replaceState) {
        window.history.replaceState( null, null, window.location.href );
    }

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
        save_asset();
    });
});


$(document).keydown(function(event) {
        if((event.ctrlKey || event.metaKey) && event.which == 83) {
            save_asset();
            event.preventDefault();
            return false;
        }
    }
);
