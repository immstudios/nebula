
/********************************************************

    AM view consists of two parts. BROWSER (left sidebar) is always visible.
    MODULE (right part) can be switched between detail rundown and scheduler.

    Browser and module state is determined by mam_context object.


    GET PARAMS
    ----------

    q : browser fulltext query
    v : browser id_view
    p : browser current page
    f : focus - id of the asset opened in detail module
    t : active tab of the detail module
        m - main
        p - preview
        t - technical
        j - jobs

*********************************************************/

context_defaults = {
    "m" : "detail",
    "q" : "",
    "v" : "",
    "p" : 1,
    "f" : "",
    "t" : "m",
    "d" : "",
    "w" : "",
    "c" : ""
};

module_params = {
    "browser"   : ["q", "v", "p"],
    "detail"    : ["f", "t"],              // t param is not here, because we do not want to reload panel
};

no_reload_params = ["t"];

mam_context = {
    "v" : 0  // force default view after first refresh
};






//
// Helper functions
//

function set_browser_highlight(id){
    $("#browser-body tr").each(function(){
        if ($(this).attr("data-href") == id) {
            $(this).addClass("active");
        } else {
            $(this).removeClass("active");
        }
      });
}

function set_browser_draggable(){
    $("#browser-body tr").draggable({
        distance: 10,
        helper: "clone",
        revert: "valid",
        appendTo: "body",
        containment: 'window',
        scroll: false,
    });
}








// After module load, this function is executed

function on_update_module(new_context) {
    var module_name = new_context["m"];

    // if module changed, highlight correct button in menu

    if (module_name != mam_context["m"]){

            set_browser_highlight(new_context["f"]);

            $("#module").on('shown.bs.tab','.detail-tab-switcher' ,function (e) {
                var target = $(e.target).attr("data-href") // activated tab
                mam_switch({ "t" : $(this).attr('data-href')});
            });


    } // end module changed

    if (module_name == "detail"){
        if (new_context["f"] != mam_context["f"])
            set_browser_highlight(new_context["f"]);
    }


} //on_update_module







// After browser load, this function is executed

function on_update_browser(new_context){
    if (new_context["q"] != mam_context["q"])
        $("#browser-search-query").val(new_context["q"]);

    if (new_context["v"] != mam_context["v"]){
        $(".view-switcher").each(function(){
            if ($(this).attr("data-href") == new_context["v"]) {
                $(this).parent().addClass("active");
                $("#view-name").html($(this).html());
            } else {
                $(this).parent().removeClass("active");
            }
        });
    }

}








function update_browser(browser_params){
    if (!(Object.keys(browser_params).length === 0))
        return $.get("/panel_browser", browser_params);
}

function update_module(module_name, update_params){
    if (!(Object.keys(update_params).length === 0))
        return $.get("/panel_"+module_name, update_params);
}



// Use this function to change MAM view context.

function mam_switch(new_params){
    var get_params = URLToArray(window.location.href);
    var new_context = {};
    for (var key in context_defaults){
        if (new_params[key])
            new_context[key] = new_params[key];
        else if (get_params[key])
            new_context[key] = get_params[key];
        else
            new_context[key] = context_defaults[key];
    }
    console.log("Updating context:", new_context);


    // set new url and save history state
    var new_get_params = {};
    for (var key in new_context){
        if (new_context[key] != context_defaults[key] && new_context[key])
            new_get_params[key] = new_context[key];
    }
    history.pushState(new_get_params, "Nebula", "/mam?" + ArrayToURL(new_get_params));


    // should we update browser or right-hand module? what?

    var do_browse = false;
    var browser_params = {};
    for (var i in module_params["browser"]){
        key = module_params["browser"][i];
        if (new_context[key] != mam_context[key]){
            console.log(key, new_context[key], mam_context[key]);
            do_browse = true;
            browser_params[key] = new_context[key];
        }
    }

    var module_name = new_context["m"];
    var do_update = false;
    var update_params = {}
    if (module_name != mam_context["m"])
        do_update = true;

    for (var i in module_params[module_name]){
        key = module_params[module_name][i];
        update_params[key] = new_context[key];
        if (no_reload_params.indexOf(key) == -1 && new_context[key] != mam_context[key])
            do_update = true;
    }


    if (!(do_browse || do_update)){
        mam_context = new_context;
        return
     }

    // wait for module and browser load
    $.when(
            update_browser(browser_params),
            update_module(module_name, update_params)
        ).done(function(browser_result, module_result){

            if (do_browse){
                if (browser_result[2]["status"] == 401)
                    window.location.href = '/';

                $("#browser").html(browser_result[0]);
                on_update_browser(new_context);
            }

            if (do_update){
                if (module_result[2]["status"] == 401)
                    window.location.href = '/';

                $("#module").html(module_result[0]);
                on_update_module(new_context);
            }

            mam_context = new_context;

        });

} // End mam_switch





//
// MAM VIEW INIT
//

$(document).ready(function() {

    //
    // Splitter
    //

    var i = 0;
    var dragging = false;
    $('#dragbar').mousedown(function (e) {
        e.preventDefault();
        dragging = true;
        var main = $('#module-wrapper');
        var ghostbar = $('<div>', {
            id: 'ghostbar',
            css: {
                height: main.outerHeight(),
                top: main.offset().top,
                left: main.offset().left
            }
        }).appendTo('body');
        $(document).mousemove(function (e) {
            ghostbar.css("left", e.pageX + 2);
        });
    });

    $(document).mouseup(function (e) {
        if (dragging) {
            $('#browser-wrapper').css("width", e.pageX + 2);
            $('#module-wrapper').css("left", e.pageX + 2);
            $('#ghostbar').remove();
            $(document).unbind('mousemove');
            dragging = false;
        }
    });


    //
    // BROWSER
    //

    // Switch browser view
    $('.view-switcher').on("click", function(){
        mam_switch({ "v" : $(this).attr('data-href'), "p" : 1});
        event.preventDefault();
    });

    $('#browser').on("click", ".page-switcher", function(){
        mam_switch({ "p" : $(this).attr('data-href')});
        event.preventDefault();
    });

    // Clear search
    $("#browser-clear-button").on("click", function( event ) {
        $("#browser-search-query").val("");
        mam_switch({"q" : $("#browser-search-query").val(), "p" : 1})
        event.preventDefault();
    });

    // Execute fulltext search
    $("#browser-search-query").keypress(function (e) {
        if (e.which == 13) { // return pressed
            mam_switch({"q" : $("#browser-search-query").val(), "p" : 1})
            event.preventDefault();
        }
    });

    $("#browser-search-button").on("click", function( event ) {
        mam_switch({"q" : $("#browser-search-query").val(), "p" : 1})
        event.preventDefault();
    });

    // Make browser rows clickable
    $("#browser").on("click", "tr[data-href]", function() {
        if (mam_context["m"] == "detail"){
            mam_switch({"f" : $(this).attr("data-href")});
            event.preventDefault();
        }
    });


    //
    // HISTORY
    //

    window.onpopstate = function(event) {
        mam_switch(event.state, false);
    };

    mam_switch({});
    console.log("MAM ready!");
});
