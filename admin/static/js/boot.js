// BOOT
$( function(){

	setTimeout( function(){
		$('#nx-flash-messages .alert-info', '#nx-flash-messages .alert-success').remove();
	}, 5000);

	setTimeout( function(){
		$('#nx-flash-messages .alert-warning').remove();
	}, 7000);

	setTimeout( function(){
		$('#nx-flash-messages .alert-danger').remove();
	}, 15000);

});

 
