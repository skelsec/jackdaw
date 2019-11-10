

var anomalies_user_row = "anomalies_user_row";
var user_pw_notexpire_table_name = "anomalies_user_pwnotexp_table";


function get_user_anomalies(d){
    document.getElementById(graph_row_name).style.visibility = "hidden";
    document.getElementById(anomalies_user_row).style.visibility = "visible";
    domainid = 1;
    url = "/anomalies/"+ domainid + "/users/";
    var json = $.getJSON(url)
    .done(function(data){        
        anom_user_populate_table(data);
    });

};

function anom_user_populate_table(data){
    var pw_notexp_table = document.getElementById(user_pw_notexpire_table_name);
    console.log(data.pw_notexp);
    console.log(data.pw_notexp[0][1]);
    for(var i = 0; i < data.pw_notexp.length; i++){
        var newRow = pw_notexp_table.insertRow(i);
        var cell = newRow.insertCell(0);
        cell.innerinnerHTML = data.pw_notexp[i][0];
        var cell = newRow.insertCell(1);
        cell.innerinnerHTML = data.pw_notexp[i][1];
    }
};

