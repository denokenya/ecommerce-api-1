from django.utils import timezone


def getValidUserData():
	dob = ( (timezone.now()-timezone.timedelta(days=21*365)) ).strftime('%Y-%m-%d')
	return {
		'first_name': 'Ken',
		'last_name': 'Alex',
		'email': 'blanka@email.com',
		'username': 'r_mika',
		'password': 'ehonda123!',
		'profile': {
			'dob': dob,
		},
		'validate': True
	}