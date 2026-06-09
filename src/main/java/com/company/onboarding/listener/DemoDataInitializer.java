/*
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

		// 1. Populating the STEPS table
		createStep("Safety briefing", 1, 10);
		createStep("Fill in profile", 1, 20);
		createStep("Check all functions", 2, 30);
		createStep("Information security training", 3, 40);
		createStep("Internal procedures studying", 5, 50);

		// 2. Populating the DEPARTMENT table
		createDepartment("Human Resources");
		createDepartment("Marketing");
		createDepartment("Operations");
		createDepartment("Finance");

		// 3. Populating the STATUS table
		createStatus("IN PROGRESS");
		createStatus("COMPLETED");

		// 3. Populating the User table
		createUser("alice", "1", "Alice", "Brown", "alice.brown@company.com");

		System.out.println(
			"✨ The database was automatically populated with test data!"
		);
	}

	private void createUser(
		String username,
		String password,
		String firstName,
		String lastName,
		String email
	) {
		User user = dm.create(User.class);
		user.setUsername(username);
		user.setPassword(encoder.encode(password));
		user.setFirstName(firstName);
		user.setLastName(lastName);
		user.setEmail(email);

		dm.save(user);
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

	private void createDepartment(String name) {
		Department department = dm.create(Department.class);
		department.setName(name);
		dm.save(department);
	}
}
*/
