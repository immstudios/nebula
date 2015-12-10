nx.com = {
	
	post : function(options){
		 
		var settings = {
			url: '',
			data: {},
			element: $('.nx-messages'),
			status: false,
			notifyDone: true,
			notifyFail: true,
			notifyError: true,
			postError: false,
			postFail: false,
			postDone: false
		};

		$.extend(settings, options);

		$.ajax({
          type: "POST",
          url: settings.url,
          dataType: 'json',
          data: settings.data,
          async: true,
          cache: false,
          error: function(jqXHR, textStatus, errorThrown){
            
             nx.utils.preloader.hide(); 
			
			if(settings.notifyError === true)
			{	
				nx.utils.alert({ 
					close: true,
					clear: true,
					type: 'danger', 
					element: settings.element, 
					message: textStatus + ' > ' + errorThrown 
				});
			}

			if(settings.postError !== false)
			{	
				nx.com.postError(settings.postError, jqXHR, textStatus, errorThrown, settings.data);
			}	
          },
          success: function(r){        
            if(r.status === false)
            {
	            if(settings.notifyFail === true)
				{	
	                nx.utils.alert({ 
	                   close: true,
	                   clear: true,
	                   type: 'warning', 
	                   element: settings.element, 
	                   message: r.reason
	                });
	            }
	                
                if(settings.postFail !== false)
				{	
			 	   nx.com.postFail(settings.postFail, r, settings.data); 
			 	}
            }else{
	            if(settings.notifyDone === true)
				{	
	                nx.utils.alert({ 
	                   close: true,
	                   clear: true,
	                   type: 'info', 
	                   element: settings.element, 
	                   message: r.reason
	                });
	            }
	                
                if(settings.postDone !== false)
                {
               		nx.com.postDone(settings.postDone, r, settings.data); 
               	}
            } 

            nx.utils.preloader.hide();    
          }
        });
	},


	postError : function(fn,a,b,c,d){
		fn(a,b,c,d);
	},

	postFail : function(fn,r,d){
		fn(r,d);
	},

	postDone : function(fn,r,d){
		fn(r,d);
	},

	get : function(){

	},

	push : function(){

	}
}


nx.utils = {

	logDev : function(r,d){
		console.log(r,d);
	},

	logError : function(a,b,c,d){
		console.log(a,b,c,d);
	},

	preloader: {
		
		show: function()
		{
			$('#site-preloader').addClass('loader');
		},
		hide: function()
		{
			$('#site-preloader').removeClass('loader');
		}
	},

	alert: function(options) {

		settings = {
			type: 'success',
			close: true,
			element: $('.nx-messages'),
			message: 'Message not set!',
			clear: false
		};

		$.extend(settings, options);

		if(settings.clear === true)
		{
			settings.element.html('');
		}

		switch (settings.type) {

			case 'info':
				_icon = '<span class="glyphicon glyphicon-info-sign"></span>';
				break;
			case 'warning':
				_icon = '<span class="glyphicon glyphicon-warning-sign"></span>';
				break;
			case 'danger':
				_icon = '<span class="glyphiconban-ban-circle"></span>';
				break;
			case 'success':
			default:
				_icon = '<span class="glyphicon glyphicon-ok-sign"></span>';

		}

		_close = settings.close === true ? '<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>' : '';
		var _alert = $('<div class="alert alert-' + settings.type + ' fade in">' + _close + '' + _icon + ' ' + settings.message + '</div>');

		settings.element.append(_alert);
	},

	isTouch: function() {
		return 'ontouchstart' in window // works on most browsers 
		|| 'onmsgesturechange' in window; // works on ie10
	}	
}

