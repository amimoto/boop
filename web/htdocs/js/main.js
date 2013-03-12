function terminal_append(data) {
// --------------------------------------------------
  oc_obj = $('#output-capture');
  oc_obj.append(data);
  oc_obj.animate({ scrollTop: oc_obj[0].scrollHeight}, 1000);
}

function terminal_monitor() {
// --------------------------------------------------
  oc_obj = $('#output-capture');
}


function command_onsubmit(event) {
// --------------------------------------------------
  event.preventDefault();

  cmd_data = this.cmd.value;
  that = this;

  terminal_append("> "+cmd_data+"\r\n");

  serialized_data = $(this).serialize();

  var request = $.ajax({
    url: "/ajax/command",
    type: "post",
    data: serialized_data,
    success: function(data, textStatus, jqXHR) {
      terminal_append(data['output']+"\r\n");
      that.cmd.value = '';
    },
    error: function(jqXHR, textStatus, errorThrown) {
      console.log("DAMN!");
    },
    xhrFields: {
      withCredentials: true
    },
  });

}

$(function(){
// --------------------------------------------------
  $('#command-form').submit(command_onsubmit);
  $('#cmd-input').focus();
});

