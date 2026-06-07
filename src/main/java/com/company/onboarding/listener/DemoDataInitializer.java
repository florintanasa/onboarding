package com.company.onboarding.listener;

import com.company.onboarding.entity.*;
import io.jmix.core.DataManager;
import io.jmix.core.security.Authenticated;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.event.ApplicationStartedEvent;
import org.springframework.context.event.EventListener;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
public class DemoDataInitializer {

	@Autowired
	private DataManager dm;

	@Autowired
	private PasswordEncoder encoder;

	@EventListener
	@Authenticated
	public void onApplicationStarted(ApplicationStartedEvent e) {
		// Check if the database was already populated in a previous run.
		if (!dm.load(Step.class).all().maxResults(1).list().isEmpty()) {
			return;
		}

		// 1. Populating the Steps directory.
		createStep("Safety briefing", 1, 10);
		createStep("Fill in profile", 1, 20);
		createStep("Check functions", 2, 30);

		// 2. Populating the Status directory.
		createStatus("ÎN_CURS");
		createStatus("FINALIZAT");

		// 3. Creating a test user with a securely encrypted BCrypt password.
		User user = dm.create(User.class);
		user.setUsername("alice");
		user.setPassword(encoder.encode("1"));
		user.setFirstName("Alice");
		user.setLastName("Brown");
		dm.save(user);

		System.out.println(
			"✨ The database was automatically populated with test data!"
		);
	}

	private void createStep(String name, Integer duration, Integer sortValue) {
		Step step = dm.create(Step.class);
		step.setName(name);
		step.setDuration(duration);
		step.setSortValue(sortValue);
		dm.save(step);
	}

	private void createStatus(String name) {
		OnboardingStatus status = dm.create(OnboardingStatus.class);
		status.setName(name);
		dm.save(status);
	}
}
