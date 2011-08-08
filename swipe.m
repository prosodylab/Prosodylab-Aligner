% slightly modified from Camacho's dissertation (appendix)
more on;

function [p,t,s] = swipep(x,fs,plim,dt,sTHR)
    if ~ exist( 'plim', 'var' ) || isempty(plim), plim = [30 5000]; end
    if ~ exist( 'dt', 'var' ) || isempty(dt), dt = 0.01; end
    dlog2p = 1/96;
    dERBs = 0.1; 
    if ~ exist( 'sTHR', 'var' ) || isempty(sTHR), sTHR = -Inf; end
    t = [ 0: dt: length(x)/fs ]'; % Times
    dc = 4; % Hop size (in cycles)
    K = 2; % Parameter k for Hann window
    % Define pitch candidates
    log2pc = [ log2(plim(1)): dlog2p: log2(plim(end)) ]';
    pc = 2 .^ log2pc;
    S = zeros( length(pc), length(t) ); % Pitch strength matrix
    % Determine P2-WSs
    logWs = round( log2( 4*K * fs ./ plim ) );
    ws = 2.^[ logWs(1): -1: logWs(2) ]; % P2-WSs
    pO = 4*K * fs ./ ws; % Optimal pitches for P2-WSs
    % Determine window sizes used by each pitch candidate
    d = 1 + log2pc - log2( 4*K*fs./ws(1) );
    % Create ERBs spaced frequencies (in Hertz)
    fERBs = erbs2hz([ hz2erbs(pc(1)/4): dERBs: hz2erbs(fs/2) ]');
    for i = 1 : length(ws)
        dn = round( dc * fs / pO(i) ); % Hop size (in samples)
        % Zero pad signal
        xzp = [ zeros( ws(i)/2, 1 ); x(:); zeros( dn + ws(i)/2, 1 ) ];
        % Compute spectrum
        w = hanning( ws(i) ); % Hann window
        o = max( 0, round( ws(i) - dn ) ); % Window overlap
        [ X, f, ti ] = specgram( xzp, ws(i), fs, w, o );
        % Interpolate at equidistant ERBs steps
        M = max( 0, interp1( f, abs(X), fERBs, 'spline', 0) ); % Magnitude
        L = sqrt( M ); % Loudness
        % Select candidates that use this window size
        if i==length(ws)
            j = find(d - i > -1);  
            k = find(d(j) - i < 0); 
        elseif i==1
            j = find(d - i < 1);
            k = find(d(j) - i > 0);
        else 
            j = find(abs(d - i) < 1); 
            k = (1:length(j))'; % transpose added by KG
        end
        Si = pitchStrengthAllCandidates( fERBs, L, pc(j) );
        % Interpolate at desired times
        if size(Si,2) > 1
            Si = interp1( ti, Si', t, 'linear', NaN )';
        else
            Si = repmat( NaN, length(Si), length(t) );
        end
        lambda = d( j(k) ) - i;
        mu = ones( size(j) );
        mu(k) = 1 - abs( lambda );
        S(j,:) = S(j,:) + repmat(mu,1,size(Si,2)) .* Si;
    end
    % Fine-tune the pitch using parabolic interpolation
    p = repmat( NaN, size(S,2), 1 );
    s = repmat( NaN, size(S,2), 1 );
    for j = 1 : size(S,2)
        [ s(j), i ] = max( S(:,j) );
        if s(j) < sTHR, continue, end
        if i==1
             p(j)=pc(1);
        elseif i==length(pc)
            p(j)=pc(1); 
        else
            I = i-1 : i+1;
            tc = 1 ./ pc(I);
            ntc = ( tc/tc(2) - 1 ) * 2*pi;
                c = polyfit( ntc, S(I,j), 2 );
            ftc = 1 ./ 2.^[ log2(pc(I(1))): 1/12/64: log2(pc(I(3))) ];
            nftc = ( ftc/tc(2) - 1 ) * 2*pi;
                [s(j) k] = max( polyval( c, nftc ) );
            p(j) = 2 ^ ( log2(pc(I(1))) + (k-1)/12/64 );
        end
    end
	p(isnan(s)) = NaN; % added by KG for 0s
end

function S = pitchStrengthAllCandidates( f, L, pc )
    % Normalize loudness
    warning off MATLAB:divideByZero
    L = L ./ repmat( sqrt( sum(L.*L) ), size(L,1), 1 );
    warning on MATLAB:divideByZero
    % Create pitch salience matrix
    S = zeros( length(pc), size(L,2) );
    for j = 1 : length(pc)
        S(j,:) = pitchStrengthOneCandidate( f, L, pc(j) );
    end
end

function S = pitchStrengthOneCandidate( f, L, pc )
    n = fix( f(end)/pc - 0.75 ); % Number of harmonics
    k = zeros( size(f) ); % Kernel
    q = f / pc; % Normalize frequency w.r.t. candidate
    for i = [ 1 primes(n) ]
        a = abs( q - i );
        % Peak's weigth
        p = a < .25;
        k(p) = cos( 2*pi * q(p) );
        % Valleys' weights
        v = .25 < a & a < .75;
        k(v) = k(v) + cos( 2*pi * q(v) ) / 2;
    end
    % Apply envelope
    k = k .* sqrt( 1./f );
    % K+-normalize kernel
    k = k / norm( k(k>0) );
    % Compute pitch strength
    S = k' * L;
end

function erbs = hz2erbs(hz)
    erbs = 21.4 * log10( 1 + hz/229 );
end

function hz = erbs2hz(erbs)
    hz = ( 10 .^ (erbs./21.4) - 1 ) * 229;
end

[x,fs] = wavread('test.wav');
[p,t,s] = swipep(x, fs, [100 600], 0.001, 0.3);
plot(p)
pause
