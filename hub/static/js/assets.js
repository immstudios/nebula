$(document).ready(function(){

    function do_search(){
        $("#form-search").submit();
    }

    $("#btn-clear").click(function(event){
        event.preventDefault();
        $("#input-query").val("");
        do_search();
    });

    $("#btn-search").click(function(event){
        event.preventDefault();
        do_search();
    });

    $("#select-view").change(function(){
        do_search();
    });

    $("#select-page").change(function(){
        do_search();
    });

    $("#input-query").keypress(function( event ) {
        if ( event.which == 13 ) {
            event.preventDefault();
            do_search();
        }
    });

    $("#browser-body").on("click", "tr[data-href]", function() {
        window.location.href = "/detail/" + $(this).attr("data-href");
    });


});

