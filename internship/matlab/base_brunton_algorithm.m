%% compute Sparse regression: sequential least squares
Xi = Theta\dXdt; % initial guess: Least-squares

% lambda is our sparsification knob.

for k=1:10
	smallinds = (abs(Xi) < lambda);   % find small coefficients
	Xi(smallinds)=0;                % and threshold
	for ind = 1:n                   % n is state dimension
		biginds = ˜smallinds(:,ind);
		
		% Regress dynamics onto remaining terms to find sparse Xi
		Xi(biginds,ind) = Theta(:,biginds)\dXdt(:,ind);
	end
end