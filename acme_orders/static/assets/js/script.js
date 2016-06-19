$(document).ready(function(){
    $('.import_ss').click(function(){
        uploadCSVFile();            
    });  
})

function uploadCSVFile(){
    file = $('#spreedsheet')[0].files[0];
    var formData = new FormData();
    formData.append('csv_file', file);

    $.ajax({
        type: 'PUT',            
        url: '/acme_orders/api/v1/orders/import',
        data: formData,
        processData: false,
        contentType: false,
        success: function(data, status, request) {
            dataStr = JSON.stringify(data)
            var obj = $.parseJSON(dataStr);
            var status_url = request.getResponseHeader('Location')                
            var div = createResultDiv();

            updateProgress(status_url, div[0]);
        },
        error: function() {
            alert('Unexpected error');
        }
    });
}

function updateProgress(status_url, div){
    $.getJSON(status_url, function(data){
        console.log(data['result']['message'])
        $(div).text(data['result']['message']);
        if( data['result']['status'] != 'SUCCESS'){
            setTimeout(function(){
                updateProgress(status_url, div);
            }, 10000);
        }
    })
}

function createResultDiv(){
    div = $('<div class="progress"></div>');
    $('#progress').append(div);
    return div;
}