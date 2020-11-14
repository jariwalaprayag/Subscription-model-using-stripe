from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from .models import Service as srv, Subscription
from django.contrib import messages
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.conf import settings
import stripe
import time
from datetime import datetime, timedelta
stripe.api_key = settings.STRIPE_API_KEY


def home(request):
    return render(request, 'home.html')


class Login(TemplateView):
    template = "login.html"

    ''' if we got a get request to this page then just display the
    login form '''

    def get(self, request):
        ''' if user is already logged in then just redirect user to
        home page '''
        if(request.user.is_authenticated):
            return redirect("home")
        ''' if user is not logged in then just render the login form '''
        return render(request, self.template, {})

    ''' if we got post request then get username and password submit to
    the page by user and check weather they are right or not '''

    def post(self, request):
        ''' taking username and password from post request '''
        username = request.POST['username']
        password = request.POST['password']
        ''' check weather user is authenticated or not '''
        user = authenticate(
            username=request.POST['username'],
            password=request.POST['password']
        )
        ''' if user is authenticated then redirect him to home page'''
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.add_message(
                request,
                messages.ERROR,
                'Incorrect username or password')
        return render(request, self.template, {})


class Logout(TemplateView):
    ''' allow user only if he is logged in '''
    @method_decorator(login_required(login_url="login/"))
    def get(self, request):
        ''' logout the user and redirect him to home '''
        logout(request)
        return redirect("login")


class Product(TemplateView):
    template = "products.html"
    model = srv

    def get(self, request):
        try:
            ''' check weather user had a subscription or not '''
            request.user.subscription
            ''' if user had a subscription in past then retrive it '''
            subscription = stripe.Subscription.retrieve(
                request.user.subscription.stripe_subscription_id)
            ''' retrive the status of subscription '''
            request.user.subscription.state = subscription.status
            ''' if subscription is cancelled '''
            if(subscription.status == "canceled"):
                ''' update the database and set it to canceled '''
                request.user.subscription.stripe_subscription_id = ""
                request.user.subscription.membership = False
                request.user.subscription.save()
            ''' if subscription is active or in trial mode '''
            if(subscription.status == "active" or
                    subscription.status == "trialing"):
                request.user.subscription.membership = True
                request.user.subscription.save()
                ''' redirect user to service page because user has
                already paid for our content '''
                return redirect("service")
            else:
                ''' if users subscription is not cancelled, active or
                trialing then redirect it to product page '''
                data = self.model.objects.all()
                service = 0
                for d in data:
                    service = service + 1
                print(service)
                return render(request, self.template, {
                    "total": service,
                    "services": data
                })
        except Subscription.DoesNotExist:
            ''' if we got exception as subscrption is not available in
            database then just redirect user to product page and display
            pricing information '''
            data = self.model.objects.all()
            service = 0
            for d in data:
                service = service + 1
            print(service)
            return render(request, self.template, {
                "total": service,
                "services": data
            })
        except stripe.error.InvalidRequestError:
            ''' if we are not able to fetch the subscription detail from
            API then also redirect user to product page and display
            pricing information '''
            data = self.model.objects.all()
            service = 0
            for d in data:
                service = service + 1
            request.user.subscription.stripe_subscription_id = ""
            request.user.subscription.membership = False
            request.user.subscription.status = "not active"
            request.user.subscription.save()
            return render(request, self.template, {
                "total": service,
                "services": data
            })


class User_service(TemplateView):
    template = "service.html"
    model = srv
    ''' only logged in user can view this information '''
    @method_decorator(login_required(login_url="login/"))
    def get(self, request, *args, **kwargs):
        try:
            ''' check weather user had a subscription or not '''
            request.user.subscription
            ''' if user had a subscription in past then retrive it '''
            subscription = stripe.Subscription.retrieve(
                request.user.subscription.stripe_subscription_id)
            ''' retrive the status of subscription '''
            request.user.subscription.state = subscription.status
            ''' if subscription is cancelled '''
            if(subscription.status == "canceled"):
                ''' update the database and set it to canceled '''
                request.user.subscription.stripe_subscription_id = ""
                request.user.subscription.membership = False
                request.user.subscription.save()
            ''' if subscription is active or in trial mode '''
            if(subscription.status == "active" or
                    subscription.status == "trialing"):
                ''' set membership boolean to true'''
                request.user.subscription.membership = True
                request.user.subscription.save()
                ''' retrive the current time '''
                t = int(time.time())
                ''' intially set trial variable to false '''
                trial = False
                ''' set days for trial to 0 initially '''
                days = 0
                ''' if subcription is in trial mode then just count how
                many days are remaining for subscription '''
                if(subscription.status == "trialing"):
                    print("in if")
                    trial = True
                    days = int((subscription.trial_end - t) / 86400) + 1
                ''' display the paid conetent to user '''
                return render(request, self.template, {
                    'cancel': subscription.cancel_at_period_end,
                    'trial': trial,
                    'days': days})
            else:
                ''' if users subscription is not cancelled, active or
                trialing then redirect it to product page '''
                return redirect("product")
        except Subscription.DoesNotExist:
            ''' if we got exception as subscrption is not available in
            database then just redirect user to product page and display
            pricing information '''
            return redirect("product")
        except stripe.error.InvalidRequestError:
            ''' if we are not able to fetch the subscription detail from
            API then also redirect user to product page and display
            pricing information '''
            request.user.subscription.membership = False
            request.user.subscription.stripe_subscription_id = ""
            request.user.subscription.status = "not active"
            request.user.subscription.save()
            return redirect("product")


class CheckOut(TemplateView):
    ''' user should be always login to process the payment'''
    @method_decorator(login_required(login_url="login/"))
    def post(self, request):
        try:
            ''' retriving the user if he had the subscription or not'''
            request.user.subscription
            subscription = stripe.Subscription.retrieve(
                request.user.subscription.stripe_subscription_id)
            ''' if user accidently endsup on checkout even if he
            has a subscription then redirect him to service page to
            display paid content  '''
            return redirect("service")
        except Subscription.DoesNotExist:
            ''' if user's subscirption does not exist then process payment'''
            try:
                ''' create the customer in stripe using stripe token
                from payment form provided by stripe'''
                stripe_customer = stripe.Customer.create(
                    email=request.user.email,
                    source=request.POST['stripeToken'])
                ''' id of out plan '''
                plan = 'price_1HOHIOHA61CYh1ap8cowUVjX'
                ''' set the trial end period after exctly 7 days '''
                trial_end = datetime.now() + timedelta(days=7)
                trial_end = int(time.mktime(trial_end.timetuple()))
                ''' create a subscription '''
                subscription = stripe.Subscription.create(
                    customer=stripe_customer.id,
                    items=[{'plan': plan}],
                    trial_end=trial_end,)
                ''' update the data of cutomer in subscirption model'''
                customer = Subscription()
                customer.user = request.user
                customer.stripeid = stripe_customer.id
                customer.membership = True
                customer.cancel_at_period_end = False
                customer.state = "trialing"
                customer.stripe_subscription_id = subscription.id
                customer.save()
                ''' redirect user to paid content '''
                return redirect("service")
            except stripe.error.CardError:
                ''' if card got declined from stripe account then
                redirect user to payment page with error message '''
                messages.add_message(
                    request,
                    messages.ERROR,
                    'Your card has been declined'
                )
                return redirect("product")
        except stripe.error.InvalidRequestError:
            ''' if user was subscriber of the service in past but
            now we dont have any information about customer's subscription
            and customer wants to restart his membership then just retrive
            the customer information without creating a new one and charge
            him for plan this scenario happens when user wants to
            restart his membership after his billing cycle end '''
            try:
                stripe_customer = stripe.Customer.retrieve(
                    request.user.subscription.stripeid)
                plan = 'price_1HOHIOHA61CYh1ap8cowUVjX'
                subscription = stripe.Subscription.create(
                    customer=stripe_customer.id,
                    items=[{'plan': plan}],)
                request.user.subscription.membership = True
                request.user.subscription.cancel_at_period_end = False
                request.user.subscription.stripe_subscription_id = \
                    subscription.id
                request.user.subscription.state = "active"
                request.user.subscription.save()
                return redirect("service")
            except stripe.error.CardError:
                ''' if card got declined from stripe account then
                redirect user to payment page with error message '''
                messages.add_message(
                    request,
                    messages.ERROR,
                    'Your card has been declined'
                )
                redirect("product")
    ''' we can not accept get request for this page so if somehow
    we got get request then just redirect used to homw page '''

    def get(self, request):
        return redirect("home")


''' this view is use to cancel the user's subscription '''


class Cancel(TemplateView):
    ''' user can access this only if they are logged in '''
    @method_decorator(login_required(login_url="login/"))
    def get(self, request):
        try:
            ''' retrive user's subscription'''
            request.user.subscription
            subscription = stripe.Subscription.retrieve(
                request.user.subscription.stripe_subscription_id)
            ''' update user's subsciption detail'''
            subscription.cancel_at_period_end = True
            subscription.save()
            ''' make an update in subscription model as well'''
            request.user.subscription.cancel_at_period_end = True
            request.user.subscription.state = "canceled"
            request.user.subscription.save()
            ''' redirect to service page '''
            return redirect("service")
        except Subscription.DoesNotExist:
            ''' if user is not having a subscription then just redirect
            him to service page'''
            return redirect("service")
        except stripe.error.InvalidRequestError:
            ''' if there is error fetching user subscription data
            then mark user's account as not active in our
            subscription model '''
            request.user.subscription.stripe_subscription_id = ""
            request.user.subscription.state = "not active"
            request.user.subscription.membership = False
            request.user.subscription.save()
            ''' redirect user to service page '''
            return redirect("service")


''' this view is used to restart the membership of user '''


class Restart(TemplateView):
    ''' user can access this only if they are logged in '''
    @method_decorator(login_required(login_url="login/"))
    def get(self, request):
        try:
            ''' retrive the user's subscription details '''
            request.user.subscription
            subscription = stripe.Subscription.retrieve(
                request.user.subscription.stripe_subscription_id)
            ''' update user's subsciption detail'''
            subscription.cancel_at_period_end = False
            subscription.save()
            ''' make an update in subscription model as well'''
            request.user.subscription.state = "active"
            request.user.subscription.cancel_at_period_end = False
            request.user.subscription.save()
            ''' redirect to service page '''
            return redirect("service")
        except Subscription.DoesNotExist:
            ''' if user is not having a subscription then just redirect
            him to product page'''
            return ("product")
        except stripe.error.InvalidRequestError:
            ''' if there is error fetching user subscription data
            then mark user's account as not active in our
            subscription model '''
            request.user.subscription.stripe_subscription_id = ""
            request.user.subscription.state = "not active"
            request.user.subscription.membership = False
            request.user.subscription.save()
            return("Product")

# Create your views here.
