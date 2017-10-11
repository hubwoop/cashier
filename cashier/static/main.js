// https://codepen.io/znak/pen/aOvMOd
contrast();

function contrast() {

	var R, G, B, C, L;

	$( "li" ).each(function() {

		R = (Math.floor(Math.random() * 256));
		G = (Math.floor(Math.random() * 256));
		B = (Math.floor(Math.random() * 256));

		$( this ).css( 'background-color', 'rgb(' + R + ',' + G + ',' + B + ')' );

		C = [ R/255, G/255, B/255 ];

		for ( var i = 0; i < C.length; ++i ) {

			if ( C[i] <= 0.03928 ) {

				C[i] = C[i] / 12.92

			} else {

				C[i] = Math.pow( ( C[i] + 0.055 ) / 1.055, 2.4);

			}

		}

		L = 0.2126 * C[0] + 0.7152 * C[1] + 0.0722 * C[2];

		if ( L > 0.179 ) {

			$( this ).css( 'color', 'black' );

		} else {

			$( this ).css( 'color', 'white' );

		}

	});

}