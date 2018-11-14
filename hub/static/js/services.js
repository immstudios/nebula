function seismic_handler(data){
	method = data[3];
	params = data[4];
	if (method == "service_state"){
        $("#service-table-body tr").each(function(){
            if ($(this).attr("data-href") == params["id"]) {
                label = "&nbsp;";
                buttons = "&nbsp;";
                autostart = "&nbsp;"

                if (params["state"] == 0){
                    label="<span class='label text-primary'>Stopped</span>";
                    buttons="<button type='button' class='service-toggle-button btn btn-sm' data-href='"+ params["id"] + "' data-action='start'>Start</button>";
                } else if (params["state"] == 1) {
                    label="<span class='label text-success'>Running</span>";
                    buttons="<button type='button' class='service-toggle-button btn btn-sm' data-href='"+ params["id"] + "' data-action='stop'>Stop</button>";
                } else if (params["state"] == 2) {
                    label="<span class='label text-warning'>Starting</span>";
                    buttons="<button type='button' class='service-toggle-button btn btn-sm' data-href='"+ params["id"] + "' disabled>...</button>";
                } else if (params["state"] == 3) {
                    label="<span class='label text-warning'>Stopping</span>";
                    buttons="<button type='button' class='service-toggle-button btn btn-sm' data-href='"+ params["id"] + "' data-action='kill'>Kill</button>";
                } else if (params["state"] == 1) {
                    label="<span class='label text-danger'>Killing</span>";
                    buttons="<button type='button' class='service-toggle-button btn btn-sm' data-href='"+ params["id"] + "' disabled>...</button>";
                }

                if (params["autostart"])
                    checked = "CHECKED";
                else
                    checked = "";

                autostart = "<div><label class='switch'><input type='checkbox' class='service-autostart-checkbox' data-href='" + params["id"] +"' "+ checked+"><span class='slider'></span></label></div>"

                $(".service-state-label", this).html(label);
                $(".service-autostart", this).html(autostart);
                $(".service-actions", this).html(buttons);
            }
        });
	} //method
} //seismic_handler


function toggle_state(id_service, new_state){
    $("#service-table-body tr[data-href='"+id_service+"'] > .service-state-label").html("Working...")
        $.ajax({
            type: "POST",
            url: "/api/system",
            data: "{\"" + new_state + "\" : " + id_service + "}",
            processData: false,
            success: function(data){
                console.log(data);
                $("#service-table-body tr[data-href='"+id_service+"'] > .service-state-label").html("Processing...")
            },
            contentType: "application/json",
            dataType: "json"
        });
}


$(document).ready(function() {
    notify = new seismicNotify(site_name, seismic_handler);
    $("#service-table").on("click", ".service-toggle-button", function(){
        toggle_state($(this).attr("data-href"), $(this).attr("data-action") );
    });

    $("#service-table").on("click", ".service-autostart-checkbox", function(){
        $.ajax({
            type: "POST",
            url: "/api/system",
            data: "{\"autostart\" : " + $(this).attr("data-href") + "}",
            processData: false,
            success: function(data){
                console.log(data);
            },
            contentType: "application/json",
            dataType: "json"
        });
    });

});
