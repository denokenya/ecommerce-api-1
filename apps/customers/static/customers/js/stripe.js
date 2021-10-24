pubKey = document.getElementById("pub-key").textContent;
var stripe = Stripe(pubKey);

// Create an instance of Elements.
var elements = stripe.elements();

// Styling
var style = {
  base: {
    color: '#32325d',
    fontFamily: '"Helvetica Neue", Helvetica, sans-serif',
    fontSmoothing: 'antialiased',
    fontSize: '16px',
    '::placeholder': {
      color: '#aab7c4'
    }
  },
  invalid: {
    color: '#fa755a',
    iconColor: '#fa755a'
  }
};

// Create an instance of the card Element.
var card = elements.create('card', {style: style});

// Add an instance of the card Element into the `card-element` <div>.
card.mount('#card-element');
// Handle real-time validation errors from the card Element.
card.on('change', function(event) {
  var displayError = document.getElementById('card-errors');
  if (event.error) {
    displayError.textContent = event.error.message;
  } else {
    displayError.textContent = '';
  }
});

form = document.getElementById("stripe-form");
form.addEventListener("submit", function(e) {
  event.preventDefault();

  stripe.createSource(card).then(function(result) {
    if (result.error) {
      // Inform the user if there was an error.
      var errorElement = document.getElementById('card-errors');
      errorElement.textContent = result.error.message;
    } else {
      // Send the token to your server.
      stripeSourceHandler(result.source);
    }
  });

  // Submit the form with the source ID.
  function stripeSourceHandler(source) {
    url = document.getElementById("url").textContent;
    csrfToken = document.getElementsByName("csrfmiddlewaretoken")[0].value;
    fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjM0ODQwMzQ5LCJqdGkiOiJhYzFkMmI3MjVmZDY0ODljYjcwN2RiMDBiYWU4OTk4YiIsInVzZXJfaWQiOjF9.EBmztkqSGFxCZW3up23FOhtbL7CtOpW12RHr-FPNXX8',
        'X-CSRFTOKEN': csrfToken
      },
      body: JSON.stringify({
        'stripe_src': source.id,
        'line1': document.getElementsByName("line1")[0].value,
        'line2': document.getElementsByName("line2")[0].value,
        'city': document.getElementsByName("city")[0].value,
        'state': document.getElementsByName("state")[0].value,
        'zipcode': document.getElementsByName("zipcode")[0].value,
        'country': document.getElementsByName("country")[0].value,
        'first_name': document.getElementsByName("first_name")[0].value,
        'last_name': document.getElementsByName("last_name")[0].value,
        'email': document.getElementsByName("email")[0].value,
      })
    })
    .then(response => response.json())
    .then(response => console.log(response))
    .catch(error => console.log(error))
  }


});