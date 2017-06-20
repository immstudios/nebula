
function zfill(nr, n, str){
    return Array(n-String(nr).length+1).join(str||'0')+nr;
}

Number.prototype.zfill = function (n,str){
    return Array(n-String(this).length+1).join(str||'0')+this;
}

var date_today = new Date();
var today = date_today.getFullYear() + "-" + (date_today.getMonth()+1).zfill(2)+ "-" + date_today.getDate().zfill(2);




function URLToArray(url) {
    var request = {};
    var idx = url.indexOf('?');
    if (idx == -1){
        return {}
    }
    var params = url.substring(idx + 1).split("#")[0];
    var pairs = params.split('&');
    for (var i = 0; i < pairs.length; i++) {
        if(!pairs[i])
            continue;
        var pair = pairs[i].split('=');
        request[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1]);
     }
     return request;
}


function ArrayToURL(array) {
    var pairs = [];
    for (var key in array){
        if (array.hasOwnProperty(key)){
            if (typeof array[key] == "undefined")
                array[key] = "";
            pairs.push(encodeURIComponent(key) + '=' + encodeURIComponent(array[key]));
        }
    }
  return pairs.join('&');
}



function seismic_handler(data){
    //console.log(data);
	method = data[3];
	params = data[4];
	if (method == "job_progress"){
        $("#job-table-body tr").each(function(){
            if ($(this).attr("data-href") == params["id"]) {
                $(".progress-bar", this).css("width", params["progress"] +"%");
                $(".job-message", this).html(params["message"]);
            }
        });
    //    console.log(params);
	}
}

$(document).ready(function() {
    notify = new seismicNotify(site_name, seismic_handler);

    $("#job-table .job-restart-button").on("click", function(){
        $.ajax({
            type: "POST",
            url: "/api/jobs",
            data: JSON.stringify({"restart" : [$(this).attr("data-href")]}),
            processData: false,
            success: function(data){ window.location.href = '/jobs/active';},
            contentType: "application/json",
            dataType: "json"
        });
    });

    $("#job-table .job-abort-button").on("click", function(){
        $.ajax({
            type: "POST",
            url: "/api/jobs",
            data: JSON.stringify({"abort" : [$(this).attr("data-href")]}),
            processData: false,
            success: function(data){ window.location.href = '/jobs/active';},
            contentType: "application/json",
            dataType: "json"
        });
    });

});
