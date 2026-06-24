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
/*
package com.florin.onboarding.listener;

import com.florin.onboarding.entity.Department;
import com.florin.onboarding.entity.OnboardingStatus;
import com.florin.onboarding.entity.Step;
import com.florin.onboarding.entity.User;
import com.florin.onboarding.entity.UserStep;
import io.jmix.core.DataManager;
import io.jmix.core.SaveContext;
import io.jmix.core.security.Authenticated;
import io.jmix.security.role.assignment.RoleAssignmentRoleType;
import io.jmix.securitydata.entity.RoleAssignmentEntity;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.event.ApplicationStartedEvent;
import org.springframework.context.event.EventListener;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
public class DemoDataInitializer {

	@Autowired
	private DataManager dataManager;

	@Autowired
	private PasswordEncoder passwordEncoder;

	@EventListener
	@Authenticated
	public void onApplicationStarted(ApplicationStartedEvent event) {
		if (
			dataManager
				.load(Step.class)
				.all()
				.maxResults(1)
				.list()
				.size() > 0
		) {
			return;
		}
		List<Step> steps = initSteps();
		List<Department> departments = initDepartments();
		List<OnboardingStatus> onboardingStatus = initOnboardingStatus();
		List<User> users = initUsers(steps, departments, onboardingStatus);
		assignRoles(users);
	}

	private List<OnboardingStatus> initOnboardingStatus() {
		OnboardingStatus onboardingStatus;
		ArrayList<OnboardingStatus> list = new ArrayList<>();

		onboardingStatus = dataManager.create(OnboardingStatus.class);
		onboardingStatus.setName("Not started");
		list.add(dataManager.save(onboardingStatus));

		onboardingStatus = dataManager.create(OnboardingStatus.class);
		onboardingStatus.setName("In progress");
		list.add(dataManager.save(onboardingStatus));

		onboardingStatus = dataManager.create(OnboardingStatus.class);
		onboardingStatus.setName("Completed");
		list.add(dataManager.save(onboardingStatus));

		return list;
	}

	private List<Step> initSteps() {
		Step step;
		ArrayList<Step> list = new ArrayList<>();

		step = dataManager.create(Step.class);
		step.setName("Safety briefing");
		step.setDuration(1);
		step.setSortValue(10);
		list.add(dataManager.save(step));

		step = dataManager.create(Step.class);
		step.setName("Fill in profile");
		step.setDuration(1);
		step.setSortValue(20);
		list.add(dataManager.save(step));

		step = dataManager.create(Step.class);
		step.setName("Check all functions");
		step.setDuration(2);
		step.setSortValue(30);
		list.add(dataManager.save(step));

		step = dataManager.create(Step.class);
		step.setName("Information security training");
		step.setDuration(3);
		step.setSortValue(40);
		list.add(dataManager.save(step));

		step = dataManager.create(Step.class);
		step.setName("Internal procedures studying");
		step.setDuration(5);
		step.setSortValue(50);
		list.add(dataManager.save(step));

		return list;
	}

	private List<Department> initDepartments() {
		Department department;
		List<Department> list = new ArrayList<>();

		department = dataManager.create(Department.class);
		department.setName("Human Resources");
		list.add(dataManager.save(department));

		department = dataManager.create(Department.class);
		department.setName("Marketing");
		list.add(dataManager.save(department));

		department = dataManager.create(Department.class);
		department.setName("Operations");
		list.add(dataManager.save(department));

		department = dataManager.create(Department.class);
		department.setName("Finance");
		list.add(dataManager.save(department));

		return list;
	}

	private List<User> initUsers(
		List<Step> steps,
		List<Department> departments,
		List<OnboardingStatus> onboardingStatus
	) {
		User user;
		SaveContext saveContext;
		List<User> list = new ArrayList<>();

		saveContext = new SaveContext();
		user = dataManager.create(User.class);
		user.setUsername("alice");
		user.setPassword(createPassword());
		user.setFirstName("Alice");
		user.setLastName("Brown");
		user.setDepartment(departments.get(0));
		saveContext.saving(user);
		list.add(user);
		for (Step step : steps) {
			UserStep userStep = dataManager.create(UserStep.class);
			userStep.setUser(user);
			userStep.setStep(step);
			userStep.setDueDate(
				LocalDate.now()
					.minusYears(2)
					.minusWeeks(3)
					.plusDays(step.getDuration())
			);
			userStep.setCompletedDate(
				LocalDate.now()
					.minusYears(2)
					.minusWeeks(3)
					.plusDays(step.getDuration() - 1)
			);
			userStep.setSortValue(step.getSortValue());
			saveContext.saving(userStep);
		}
		dataManager.save(saveContext);

		Department marketingDept = departments.get(1);
		marketingDept.setHrManager(user);
		dataManager.save(marketingDept);

		saveContext = new SaveContext();
		user = dataManager.create(User.class);
		user.setUsername("james");
		user.setPassword(createPassword());
		user.setFirstName("James");
		user.setLastName("Wilson");
		user.setDepartment(departments.get(0));
		saveContext.saving(user);
		list.add(user);
		for (Step step : steps) {
			UserStep userStep = dataManager.create(UserStep.class);
			userStep.setUser(user);
			userStep.setStep(step);
			userStep.setDueDate(
				LocalDate.now()
					.minusYears(1)
					.minusWeeks(5)
					.plusDays(step.getDuration())
			);
			userStep.setCompletedDate(
				LocalDate.now()
					.minusYears(1)
					.minusWeeks(5)
					.plusDays(step.getDuration() - 1)
			);
			userStep.setSortValue(step.getSortValue());
			saveContext.saving(userStep);
		}
		dataManager.save(saveContext);

		Department operationsDept = departments.get(2);
		operationsDept.setHrManager(user);
		dataManager.save(operationsDept);

		saveContext = new SaveContext();
		user = dataManager.create(User.class);
		user.setUsername("mary");
		user.setPassword(createPassword());
		user.setFirstName("Mary");
		user.setLastName("Jones");
		user.setDepartment(departments.get(1));
		user.setOnboardingStatus(onboardingStatus.get(0));
		saveContext.saving(user);
		list.add(user);
		for (Step step : steps) {
			UserStep userStep = dataManager.create(UserStep.class);
			userStep.setUser(user);
			userStep.setStep(step);
			userStep.setDueDate(
				LocalDate.now().minusDays(3).plusDays(step.getDuration())
			);
			userStep.setCompletedDate(null);
			userStep.setSortValue(step.getSortValue());
			saveContext.saving(userStep);
		}
		dataManager.save(saveContext);

		saveContext = new SaveContext();
		user = dataManager.create(User.class);
		user.setUsername("linda");
		user.setPassword(createPassword());
		user.setFirstName("Linda");
		user.setLastName("Evans");
		user.setDepartment(departments.get(2));
		user.setOnboardingStatus(onboardingStatus.get(1));
		saveContext.saving(user);
		list.add(user);
		for (Step step : steps) {
			UserStep userStep = dataManager.create(UserStep.class);
			userStep.setUser(user);
			userStep.setStep(step);
			userStep.setDueDate(
				LocalDate.now().minusDays(2).plusDays(step.getDuration())
			);
			userStep.setCompletedDate(null);
			userStep.setSortValue(step.getSortValue());
			saveContext.saving(userStep);
		}
		dataManager.save(saveContext);

		saveContext = new SaveContext();
		user = dataManager.create(User.class);
		user.setUsername("susan");
		user.setPassword(createPassword());
		user.setFirstName("Susan");
		user.setLastName("Baker");
		user.setDepartment(departments.get(2));
		user.setOnboardingStatus(onboardingStatus.get(2));
		saveContext.saving(user);
		list.add(user);
		for (Step step : steps) {
			UserStep userStep = dataManager.create(UserStep.class);
			userStep.setUser(user);
			userStep.setStep(step);
			userStep.setDueDate(LocalDate.now().plusDays(step.getDuration()));
			userStep.setCompletedDate(null);
			userStep.setSortValue(step.getSortValue());
			saveContext.saving(userStep);
		}
		dataManager.save(saveContext);

		saveContext = new SaveContext();
		user = dataManager.create(User.class);
		user.setUsername("bob");
		user.setPassword(createPassword());
		user.setFirstName("Robert");
		user.setLastName("Taylor");
		user.setDepartment(departments.get(2));
		user.setOnboardingStatus(onboardingStatus.get(2));
		saveContext.saving(user);
		list.add(user);
		for (Step step : steps) {
			UserStep userStep = dataManager.create(UserStep.class);
			userStep.setUser(user);
			userStep.setStep(step);
			userStep.setDueDate(
				LocalDate.now().minusDays(1).plusDays(step.getDuration())
			);
			userStep.setCompletedDate(
				userStep.getDueDate().isBefore(LocalDate.now().plusDays(1))
					? userStep.getDueDate()
					: null
			);
			userStep.setSortValue(step.getSortValue());
			saveContext.saving(userStep);
		}
		dataManager.save(saveContext);

		return list;
	}

	private String createPassword() {
		return passwordEncoder.encode("1");
	}

	private void assignRoles(List<User> users) {
		for (User user : users) {
			boolean isHrManager = Arrays.asList("alice", "james").contains(
				user.getUsername()
			);

			RoleAssignmentEntity roleAssignment;

			roleAssignment = dataManager.create(RoleAssignmentEntity.class);
			roleAssignment.setUsername(user.getUsername());
			roleAssignment.setRoleCode("ui-minimal");
			roleAssignment.setRoleType(RoleAssignmentRoleType.RESOURCE);
			dataManager.save(roleAssignment);

			roleAssignment = dataManager.create(RoleAssignmentEntity.class);
			roleAssignment.setUsername(user.getUsername());
			roleAssignment.setRoleCode(
				isHrManager ? "hr-manager" : "employee-role"
			);
			roleAssignment.setRoleType(RoleAssignmentRoleType.RESOURCE);
			dataManager.save(roleAssignment);

			if (isHrManager) {
				roleAssignment = dataManager.create(RoleAssignmentEntity.class);
				roleAssignment.setUsername(user.getUsername());
				roleAssignment.setRoleCode("hr-manager");
				roleAssignment.setRoleType(RoleAssignmentRoleType.ROW_LEVEL);
				dataManager.save(roleAssignment);
			}
		}
	}
}

 */