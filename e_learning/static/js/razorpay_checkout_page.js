document.addEventListener('DOMContentLoaded', function () {
  const payButton = document.getElementById('razorpay-pay-button');
  if (!payButton) {
    return;
  }

  payButton.addEventListener('click', function () {
    const checkout = new Razorpay({
      key: window.RAZORPAY_KEY_ID,
      amount: window.RAZORPAY_AMOUNT,
      currency: 'INR',
      name: 'E-Learning',
      description: window.RAZORPAY_COURSE_NAME,
      order_id: window.RAZORPAY_ORDER_ID,
      prefill: {
        name: window.RAZORPAY_NAME || '',
        email: window.RAZORPAY_EMAIL || '',
        contact: window.RAZORPAY_CONTACT || '',
      },
      notes: {
        course_id: window.RAZORPAY_COURSE_ID || '',
        user_id: window.RAZORPAY_USER_ID || '',
      },
      theme: { color: '#0d6efd' },
      modal: {
        escape: true,
        ondismiss: function () {
          console.log('Razorpay checkout dismissed');
        }
      }
    });
    checkout.open();
  });
});
