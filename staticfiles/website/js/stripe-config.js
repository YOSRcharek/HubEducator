// Initialize Stripe with the public key
let stripe;
let elements;

document.addEventListener('DOMContentLoaded', function() {
    // Get the public key from the data attribute
    const stripePublicKey = document.getElementById('payment-form').dataset.stripeKey;
    stripe = Stripe(stripePublicKey);
    elements = stripe.elements();
    
    // Create card element
    const cardElement = elements.create('card', {
        style: {
            base: {
                fontSize: '16px',
                color: '#32325d',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                '::placeholder': {
                    color: '#aab7c4'
                }
            },
            invalid: {
                color: '#fa755a',
                iconColor: '#fa755a'
            }
        }
    });
    
    // Mount card element
    cardElement.mount('#card-element');
    
    // Handle card errors
    cardElement.on('change', function(event) {
        const displayError = document.getElementById('card-errors');
        if (event.error) {
            displayError.textContent = event.error.message;
        } else {
            displayError.textContent = '';
        }
    });
    
    // Handle form submission
    const form = document.getElementById('payment-form');
    const submitButton = document.getElementById('submit-button');
    const buttonText = document.getElementById('button-text');
    const spinner = document.getElementById('spinner');
    
    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        
        // Disable submit button
        submitButton.disabled = true;
        buttonText.classList.add('d-none');
        spinner.classList.remove('d-none');
        
        const cardholderName = document.getElementById('card_name').value;
        
        // Get client secret from the data attribute
        const clientSecret = form.dataset.clientSecret;
        
        // Confirm payment with Stripe
        const {error, paymentIntent} = await stripe.confirmCardPayment(
            clientSecret,
            {
                payment_method: {
                    card: cardElement,
                    billing_details: {
                        name: cardholderName
                    }
                }
            }
        );
        
        if (error) {
            // Show error to customer
            const errorElement = document.getElementById('card-errors');
            errorElement.textContent = error.message;
            
            // Re-enable submit button
            submitButton.disabled = false;
            buttonText.classList.remove('d-none');
            spinner.classList.add('d-none');
        } else {
            // Payment succeeded, redirect to success page
            if (paymentIntent.status === 'succeeded') {
                // Submit form to process_payment to save transaction
                const processForm = document.createElement('form');
                processForm.method = 'POST';
                processForm.action = form.dataset.processUrl;
                
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = csrfToken;
                processForm.appendChild(csrfInput);
                
                document.body.appendChild(processForm);
                processForm.submit();
            }
        }
    });
});