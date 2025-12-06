from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth
from app import db
from datetime import datetime, timedelta
import razorpay
import os

bp = Blueprint('payments', __name__, url_prefix='/api/payments')

# Initialize Razorpay
razorpay_client = razorpay.Client(
    auth=(os.getenv('RAZORPAY_KEY_ID'), os.getenv('RAZORPAY_KEY_SECRET'))
)

PLANS = {
    'basic_monthly': {
        'name': 'Basic Monthly',
        'price': 499,  # INR
        'duration_days': 30,
        'features': ['View Contact Details', 'Unlimited Messages', 'Priority Support']
    },
    'premium_monthly': {
        'name': 'Premium Monthly',
        'price': 999,
        'duration_days': 30,
        'features': ['All Basic Features', 'Profile Boost', 'See Who Viewed You', 'Advanced Filters']
    },
    'premium_yearly': {
        'name': 'Premium Yearly',
        'price': 9999,
        'duration_days': 365,
        'features': ['All Premium Features', '2 Months Free', 'Priority Matching']
    }
}

@bp.route('/plans', methods=['GET'])
def get_plans():
    """Get all subscription plans"""
    return jsonify({
        "success": True,
        "plans": PLANS
    })

@bp.route('/create-order', methods=['POST'])
@require_auth
def create_order():
    """Create Razorpay order"""
    try:
        data = request.json
        plan_id = data.get('planId')
        
        if plan_id not in PLANS:
            return jsonify({"error": "Invalid plan"}), 400
        
        plan = PLANS[plan_id]
        amount = plan['price'] * 100  # Convert to paise
        
        # Create Razorpay order
        order = razorpay_client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1
        })
        
        # Store order in database
        db.collection('payments').add({
            'userId': request.user_id,
            'orderId': order['id'],
            'planId': plan_id,
            'amount': plan['price'],
            'currency': 'INR',
            'status': 'created',
            'createdAt': datetime.utcnow()
        })
        
        return jsonify({
            "success": True,
            "order": order,
            "plan": plan
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/verify-payment', methods=['POST'])
@require_auth
def verify_payment():
    """Verify payment and activate subscription"""
    try:
        data = request.json
        order_id = data.get('orderId')
        payment_id = data.get('paymentId')
        signature = data.get('signature')
        
        # Verify signature
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Get payment record
        payment_query = db.collection('payments')\
            .where('orderId', '==', order_id)\
            .limit(1)\
            .get()
        
        if not payment_query:
            return jsonify({"error": "Payment not found"}), 404
        
        payment_doc = payment_query[0]
        payment_data = payment_doc.to_dict()
        plan_id = payment_data['planId']
        plan = PLANS[plan_id]
        
        # Update payment status
        db.collection('payments').document(payment_doc.id).update({
            'paymentId': payment_id,
            'signature': signature,
            'status': 'completed',
            'completedAt': datetime.utcnow()
        })
        
        # Activate premium subscription
        expiry_date = datetime.utcnow() + timedelta(days=plan['duration_days'])
        
        db.collection('users').document(request.user_id).update({
            'isPremium': True,
            'premiumPlan': plan_id,
            'premiumActivatedAt': datetime.utcnow(),
            'premiumExpiresAt': expiry_date
        })
        
        # Send confirmation notification
        db.collection('notifications').add({
            'userId': request.user_id,
            'type': 'payment_success',
            'title': 'Premium Activated',
            'message': f'Your {plan["name"]} subscription is now active!',
            'read': False,
            'createdAt': datetime.utcnow()
        })
        
        return jsonify({
            "success": True,
            "message": "Payment verified and premium activated",
            "expiresAt": expiry_date.isoformat()
        })
        
    except razorpay.errors.SignatureVerificationError:
        return jsonify({"error": "Invalid payment signature"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/subscription-status', methods=['GET'])
@require_auth
def get_subscription_status():
    """Get current subscription status"""
    try:
        user_doc = db.collection('users').document(request.user_id).get()
        
        if not user_doc.exists:
            return jsonify({"error": "User not found"}), 404
        
        user_data = user_doc.to_dict()
        
        is_premium = user_data.get('isPremium', False)
        expires_at = user_data.get('premiumExpiresAt')
        
        # Check if expired
        if is_premium and expires_at:
            if datetime.utcnow() > expires_at:
                # Deactivate premium
                db.collection('users').document(request.user_id).update({
                    'isPremium': False
                })
                is_premium = False
        
        return jsonify({
            "success": True,
            "isPremium": is_premium,
            "plan": user_data.get('premiumPlan') if is_premium else None,
            "expiresAt": expires_at.isoformat() if expires_at else None
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500